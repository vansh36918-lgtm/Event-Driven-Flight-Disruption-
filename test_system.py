"""
Automated Test & Verification Suite.
Validates GDS Inventory, NetworkX Graph Re-Routing Engine, Event Broker, and AI Concierge.
"""
import sys
import os
import asyncio
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.engine.gds_service import gds_service
from app.engine.graph_engine import reaccommodation_engine
from app.worker.reaccommodation_worker import reaccommodation_worker
from app.bus.event_broker import event_broker
from app.ai.assistant import ai_assistant
from app.models.schemas import DisruptionWebhookPayload, DisruptionType


def test_gds_inventory():
    print("Testing GDS Inventory & PNR Generation...")
    flights = gds_service.list_flights(100)
    assert len(flights) > 0, "No flights generated in GDS!"
    assert len(gds_service.pnrs) > 0, "No PNRs generated in GDS!"

    # Validate 6-character uppercase alphanumeric PNR standard
    for pnr_id in list(gds_service.pnrs.keys())[:20]:
        assert len(pnr_id) == 6, f"PNR {pnr_id} length is not 6!"
        assert pnr_id.isalnum(), f"PNR {pnr_id} is not alphanumeric!"
        assert pnr_id.isupper(), f"PNR {pnr_id} is not uppercase!"

    print(f"  [OK] Generated {len(flights)} flights and {len(gds_service.pnrs)} PNRs.")


def test_graph_engine():
    print("Testing NetworkX Constrained Route Engine (4-hour window)...")
    all_flights = list(gds_service.flights.values())
    reaccommodation_engine.build_schedule_graph(all_flights)

    # Pick a flight to test
    sample_flight = all_flights[0]
    alternatives = reaccommodation_engine.find_alternatives(
        origin=sample_flight.origin,
        destination=sample_flight.destination,
        original_departure=sample_flight.departure_time,
        max_window_hours=4,
    )

    print(f"  Route: {sample_flight.origin} -> {sample_flight.destination}")
    print(f"  Found {len(alternatives)} alternative routes within 4-hour departure window.")
    for alt in alternatives:
        assert alt.departure_delay_minutes <= 240, "Alternative departs outside 4-hour window!"
        print(f"   - {alt.option_id} | Type: {alt.route_type} | Delay: +{alt.departure_delay_minutes}m")
    print("  [OK] Constrained graph search passed.")


async def test_event_pipeline_and_ai():
    print("Testing Event Pipeline & Passenger AI Concierge...")
    # Subscribe worker to broker
    event_broker.subscribe(reaccommodation_worker.handle_disruption_event)

    # Pick a flight with booked passengers
    target_flight_num = None
    for f_num, pnr_list in gds_service.flight_to_pnrs.items():
        if len(pnr_list) > 0:
            target_flight_num = f_num
            break

    assert target_flight_num is not None, "No flight with passengers found!"
    target_flight = gds_service.get_flight(target_flight_num)
    sample_pnr = gds_service.flight_to_pnrs[target_flight_num][0]
    passenger = gds_service.get_pnr(sample_pnr)

    print(f"  Simulating disruption for flight {target_flight_num} (Affected passenger: {passenger.passenger_name}, PNR: {sample_pnr})...")

    # 1. Trigger disruption webhook
    payload = DisruptionWebhookPayload(
        event_id="TEST-EVT-001",
        disruption_type=DisruptionType.CANCELLATION,
        flight_number=target_flight_num,
        carrier=target_flight.carrier,
        origin=target_flight.origin,
        destination=target_flight.destination,
        scheduled_departure=target_flight.departure_time,
        reason="Mechanical malfunction at gate",
    )
    gds_service.record_disruption(payload)
    await reaccommodation_worker.handle_disruption_event(payload.model_dump(mode="json"))

    # 2. Check PNR state transition
    pnr_after = gds_service.get_pnr(sample_pnr)
    assert pnr_after.status == "DISRUPTED", f"Expected status DISRUPTED, got {pnr_after.status}"
    assert len(pnr_after.reaccommodation_options) > 0, "Worker failed to populate alternative options!"
    print(f"  [OK] Passenger PNR {sample_pnr} transitioned to DISRUPTED with {len(pnr_after.reaccommodation_options)} options.")

    # 3. AI Concierge Inquiry
    response_inquiry = await ai_assistant.chat(pnr_id=sample_pnr, user_message="What happened to my flight? Show me alternatives.")
    assert response_inquiry.detected_intent == "DISRUPTION_INQUIRY"
    print(f"  AI Inquiry Response:\n    {response_inquiry.reply[:120]}...")

    # 4. AI Concierge Confirmation
    response_rebook = await ai_assistant.chat(pnr_id=sample_pnr, user_message="Please confirm and book me on Option 1")
    assert response_rebook.detected_intent == "CONFIRM_REBOOK"
    assert gds_service.get_pnr(sample_pnr).status == "RE_ACCOMMODATED"
    print(f"  AI Re-Ticketing Response:\n    {response_rebook.reply[:120]}...")
    print(f"  [OK] PNR {sample_pnr} successfully re-accommodated via AI concierge!")

    # 5. Compensation & Boarding Pass Verification
    from app.engine.compensation_engine import compensation_engine
    pnr_final = gds_service.get_pnr(sample_pnr)
    comp = compensation_engine.calculate_entitlements(pnr_final)
    assert comp["cash_compensation_usd"] >= 250, "Expected minimum $250 compensation entitlement!"
    assert comp["vouchers"]["meal_voucher_code"].startswith("VCH-MEAL"), "Invalid meal voucher code!"
    
    bp = compensation_engine.generate_boarding_pass(pnr_final)
    assert bp["pnr_id"] == sample_pnr
    assert len(bp["seat"]) in [2, 3]  # e.g. 12B or 4A
    assert len(bp["qr_data"]) > 10
    print(f"  [OK] EU261/DOT Compensation ({comp['haul_tier']} - ${comp['cash_compensation_usd']}) & Boarding Pass verified!")

    # 6. IATA NDC 21.3 Order Payload & PVS Verification
    from app.engine.ndc_service import ndc_service
    assert 100 <= pnr_final.pvs_score <= 1000, f"Invalid PVS score: {pnr_final.pvs_score}"
    ndc_payload = ndc_service.generate_order_change_notification(
        pnr_final, target_flight, pnr_final.reaccommodation_options[0]["segments"]
    )
    assert "IATA_OrderChangeNotifRQ" in ndc_payload, "Missing IATA_OrderChangeNotifRQ root tag!"
    order = ndc_payload["IATA_OrderChangeNotifRQ"]["Order"]
    assert order["StatusCode"] == "CONFIRMED"
    print(f"  [OK] IATA NDC 21.3 OrderChangeNotifRQ generated ({order['OrderID']}) with PVS score {pnr_final.pvs_score}!")

    # 7. IATA NDC 21.3 OrderReshopRS Verification
    reshop_payload = ndc_service.generate_order_reshop_response(pnr_final, pnr_final.reaccommodation_options)
    assert "IATA_OrderReshopRS" in reshop_payload, "Missing IATA_OrderReshopRS tag!"
    offers = reshop_payload["IATA_OrderReshopRS"]["ReshopOffers"]
    assert len(offers) >= 2, "Expected at least 2 reshop offer bundles!"
    print(f"  [OK] IATA NDC 21.3 OrderReshopRS generated with {len(offers)} dynamic offer bundles!")

    # 8. FAA Part 117 Crew Pairing Cascading Timeout Verification
    from app.engine.crew_engine import crew_engine
    cascading_alerts = crew_engine.evaluate_cascading_timeout("AA100", delay_minutes=240)
    assert len(cascading_alerts) > 0, "Expected downstream crew timeouts on rotation CP-101!"
    print(f"  [OK] FAA Part 117 Crew Pairing engine caught {len(cascading_alerts)} cascading timeout violations for rotation!")

    # 9. Aircraft Fleet Assignment & Tail-Swap Verification
    from app.engine.fleet_engine import fleet_engine
    swap = fleet_engine.evaluate_tail_swap("AA100", "JFK", "AA")
    assert swap is not None, "Expected operational tail-swap to execute at JFK hub!"
    assert swap["action"] == "TAIL_SWAP_EXECUTED"
    print(f"  [OK] Aircraft Tail-Swap executed ({swap['original_tail']} -> {swap['assigned_spare_tail']}) at {swap['hub']}!")

    # 10. FAA Ground Delay Program & CDM Slot Substitution Verification
    from app.engine.slot_engine import slot_engine
    active_gdps = slot_engine.get_active_gdps()
    assert len(active_gdps) > 0, "Expected active GDP at ORD!"
    slot_swap = slot_engine.optimize_slot_substitution("AA100", "AAFeeder99", "ORD")
    assert slot_swap is not None, "Expected CDM slot swap optimization!"
    assert slot_swap["action"] == "CDM_SLOT_SWAP_CONFIRMED"
    print(f"  [OK] FAA ATC Ground Delay Program & CDM Slot Swap verified ({slot_swap['protected_slot']} saved {slot_swap['pax_delay_minutes_saved']}m delay)!")

    # 11. Airline Alliance & IATA Rule 240 Involuntary Endorsement Verification
    from app.engine.alliance_engine import alliance_engine
    assert alliance_engine.get_alliance("UA") == "STAR_ALLIANCE"
    assert alliance_engine.get_alliance("AA") == "ONEWORLD"
    assert alliance_engine.get_alliance("DL") == "SKYTEAM"
    assert alliance_engine.compute_affinity_score("AA", "AA") == 1.0
    assert alliance_engine.compute_affinity_score("AA", "BA") == 0.90
    assert alliance_engine.check_interline_baggage_through_check("AA", "BA") is True
    endorsement = alliance_engine.generate_rule_240_endorsement("AA", "UA", "TEST01")
    assert "RULE 240" in endorsement["endorsement_string"]
    assert endorsement["protocol"] == "RULE_240_INVOLUNTARY"
    print(f"  [OK] Airline Alliance Matrix & IATA Rule 240 Involuntary Endorsement verified ({endorsement['protocol']})!")

    # 12. IATA IRROPS Incident Post-Mortem & Regulatory Audit Verification
    from app.engine.audit_engine import audit_engine
    report = audit_engine.generate_incident_post_mortem()
    assert "incident_report_id" in report, "Missing incident_report_id in audit report!"
    assert "financial_impact_usd" in report, "Missing financial_impact_usd in audit report!"
    assert report["financial_impact_usd"]["labor_cost_savings_usd"] >= 0
    assert "pax_segmentation" in report
    print(f"  [OK] IATA IRROPS Incident Post-Mortem Audit Report generated ({report['incident_report_id']}) with financial ROI!")

    # 13. IATA Res 766 Operational Cabin Upgrade (Op-Up) & Printable Audit Markdown Dossier
    pnr_final.pvs_score = 750
    from app.models.schemas import FareClass
    pnr_final.fare_class = FareClass.ECONOMY
    pnr_upgraded = gds_service.confirm_pnr_rebook(pnr_final.pnr_id, pnr_final.reaccommodation_options[0]["option_id"])
    assert pnr_upgraded.upgraded_cabin == "BUSINESS (CLASS J)"
    assert "IATA RES 766" in pnr_upgraded.upgrade_reason
    md_dossier = audit_engine.generate_incident_post_mortem_markdown()
    assert "# IATA IRROPS INCIDENT POST-MORTEM" in md_dossier
    assert "TOTAL PLATFORM NET ROI" in md_dossier
    print(f"  [OK] IATA Res 766 Op-Up ({pnr_upgraded.upgraded_cabin}) & Printable Audit Dossier verified!")

    # 14. IATA Resolution 753 Baggage Tracking & RFID Auto-Reroute Verification
    from app.engine.baggage_engine import baggage_engine
    bag_rec = baggage_engine.get_baggage_record(pnr_final.pnr_id)
    assert bag_rec is not None, "Expected baggage tracking record!"
    assert len(bag_rec["iata_tag_number"]) == 10, f"Expected 10-digit IATA barcode, got {bag_rec['iata_tag_number']}"
    assert len(bag_rec["rfid_scan_history"]) >= 4, "Expected all 4 mandatory IATA 753 custody checkpoints!"
    assert "BSM/" in bag_rec["sita_bagmessage"]
    print(f"  [OK] IATA Res 753 Baggage Tracking & RFID Auto-Reroute verified (Tag: {bag_rec['iata_tag_number']}, Bay: {bag_rec['bhs_sorter_bay']})!")

    # 15. Reserve Crew Deadhead Recovery & CRS E-Hotel Voucher Verification
    from app.engine.crew_engine import crew_engine
    from app.engine.hotel_engine import hotel_engine

    # Test Reserve Crew Deadhead Recovery
    reserves = crew_engine.get_reserve_pool("ORD")
    assert len(reserves) >= 2, "Expected standby reserve crew at ORD hub!"
    crew_dispatch = crew_engine.execute_deadhead_recovery("B6101", hub="ORD")
    assert crew_dispatch is not None, "Expected crew recovery dispatch for B6101!"
    assert crew_dispatch.duty_legality == "FAA_PART_117_CERTIFIED_LEGAL"
    assert "Capt." in crew_dispatch.assigned_captain
    assert "F/O" in crew_dispatch.assigned_first_officer
    assert len(crew_engine.get_recovery_dispatches()) >= 1

    # Test CRS / Sabre E-Hotel and Meal Voucher Generation
    hotel_vch = hotel_engine.issue_hotel_voucher(
        pnr_id=pnr_final.pnr_id,
        passenger_name=pnr_final.passenger_name,
        disrupted_flight_num=pnr_final.original_flight_number,
        hub_airport="ORD",
        cabin_class="BUSINESS",
        pvs_score=pnr_final.pvs_score,
        force=True,
    )
    assert hotel_vch is not None, "Expected hotel voucher for disrupted passenger!"
    assert hotel_vch.room_tier == "EXECUTIVE_SUITE"  # Upgraded / high PVS
    assert hotel_vch.meal_stipend_usd == 95.0
    assert "SABRE-DIRBILL-" in hotel_vch.corporate_direct_bill
    assert "VOUCHER:" in hotel_vch.qr_payload
    retrieved_vch = hotel_engine.get_voucher_by_pnr(pnr_final.pnr_id)
    assert retrieved_vch is not None and retrieved_vch.voucher_id == hotel_vch.voucher_id
    print(f"  [OK] Reserve Crew Deadhead ({crew_dispatch.assigned_captain} & {crew_dispatch.assigned_first_officer}) & CRS E-Hotel Voucher ({hotel_vch.voucher_id} at {hotel_vch.hotel_name}) verified!")

    # 16. Airborne In-Flight Diversion & Alternate Hub Intermodal Ground Engine Verification
    from app.engine.divert_engine import divert_engine
    div_rec = divert_engine.execute_flight_diversion(
        flight_number="UA100",
        origin="JFK",
        destination="ORD",
        carrier="UA",
        affected_passengers=160,
        reason="Severe Squall Line Convective Activity - ORD Runway 10C/28C Closed",
    )
    assert div_rec is not None, "Expected flight diversion record!"
    assert div_rec.diverted_airport == "MKE", f"Expected ORD alternate MKE, got {div_rec.diverted_airport}"
    assert div_rec.resolution_type == "INTERMODAL_COACH_DISPATCH"
    assert div_rec.coach_dispatch is not None
    assert div_rec.coach_dispatch.transit_duration_minutes == 85
    assert div_rec.coach_dispatch.arrival_hub == "ORD"
    assert "AIR-OPS-" in div_rec.coach_dispatch.bus_plaque_code
    assert divert_engine.get_diversion_by_flight("UA100") is not None
    print(f"  [OK] Airborne Diversion ({div_rec.flight_number} -> {div_rec.diverted_airport}) & Intermodal Coach Dispatch ({div_rec.coach_dispatch.dispatch_id} to {div_rec.coach_dispatch.arrival_hub}) verified!")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING VERIFICATION TEST SUITE (GSD SPEC)")
    print("=" * 60)
    test_gds_inventory()
    test_graph_engine()
    asyncio.run(test_event_pipeline_and_ai())
    print("=" * 60)
    print("ALL TESTS PASSED WITH ZERO REGRESSIONS!")
    print("=" * 60)

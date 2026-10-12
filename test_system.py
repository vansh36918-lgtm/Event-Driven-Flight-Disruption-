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

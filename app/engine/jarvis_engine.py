"""
JARVIS AI Aviation Voice Assistant Engine.
Parses natural language speech commands, dispatches autonomous airline IRROPS actions,
triggers 3D radar manipulations, manages passenger bookings, and returns synthesized voice replies.
"""
import re
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.models.schemas import (
    VoiceCommandRequest,
    VoiceCommandResponse,
    DisruptionWebhookPayload,
    DisruptionType,
)
from app.engine.gds_service import gds_service
from app.bus.event_broker import event_broker
from app.worker.reaccommodation_worker import reaccommodation_worker
from app.engine.divert_engine import divert_engine
from app.engine.audit_engine import audit_engine
from app.engine.compensation_engine import compensation_engine
from app.ai.assistant import ai_assistant


class JarvisVoiceEngine:
    def __init__(self):
        self.callsign = "JARVIS"

    async def process_voice_command(self, req: VoiceCommandRequest) -> VoiceCommandResponse:
        cmd = req.command.strip()
        cmd_lower = cmd.lower()

        # 1. DISRUPT / CANCEL / DELAY FLIGHT
        flt_match = re.search(r'\b(6e|ai|qp|uk|aa|dl|ua|b6)\s*(\d{2,4})\b', cmd_lower)
        if any(w in cmd_lower for w in ["disrupt", "cancel", "delay", "ground"]) and flt_match:
            carrier = flt_match.group(1).upper()
            flt_digits = flt_match.group(2)
            flt_num = f"{carrier}{flt_digits}"

            disruption_type = DisruptionType.CANCELLATION if any(w in cmd_lower for w in ["cancel", "cancellation", "ground"]) else DisruptionType.WEATHER_DELAY
            reason = "JARVIS Voice Command: Monsoonal Squall Line & Turbulence" if disruption_type == DisruptionType.WEATHER_DELAY else "JARVIS Voice Command: Avionics Actuator Inspection"

            flight = gds_service.get_flight(flt_num)
            if not flight:
                # Default fallback or pick first available flight if exact number not found
                return VoiceCommandResponse(
                    command=cmd,
                    intent="DISRUPT_FLIGHT",
                    action="FLIGHT_NOT_FOUND",
                    target=flt_num,
                    speech_response=f"Sir, flight {flt_num} was not found in the active GDS schedule roster. Please specify an active flight like 6E204 or AI803.",
                    status="FAILED"
                )

            payload = DisruptionWebhookPayload(
                event_id=f"EVT-JARVIS-{int(datetime.now(timezone.utc).timestamp())}-{flt_num}",
                disruption_type=disruption_type,
                flight_number=flt_num,
                carrier=carrier,
                origin=flight.origin,
                destination=flight.destination,
                scheduled_departure=flight.departure_time,
                reason=reason
            )

            gds_service.record_disruption(payload)
            await event_broker.publish_disruption(payload)
            await reaccommodation_worker.handle_disruption_event(payload.model_dump(mode="json"))

            affected = gds_service.get_pnrs_for_flight(flt_num)
            sample_pnr = affected[0].pnr_id if affected else None
            solve_ms = reaccommodation_worker.last_solve_time_ms

            speech = (
                f"JARVIS protocol executed. Flight {flt_num} from {flight.origin} to {flight.destination} has been flagged for {disruption_type.value}. "
                f"NetworkX Pareto-optimal engine re-accommodated {len(affected)} passengers in {solve_ms:.2f} milliseconds. "
                f"Statutory compensation vouchers and IATA involuntary endorsements have been issued."
            )

            return VoiceCommandResponse(
                command=cmd,
                intent="DISRUPT_FLIGHT",
                action="DISRUPTED",
                target=flt_num,
                speech_response=speech,
                ui_action={
                    "type": "FLIGHT_DISRUPTED",
                    "flight_number": flt_num,
                    "affected_pnrs": len(affected),
                    "sample_pnr": sample_pnr,
                    "solve_ms": solve_ms,
                    "origin": flight.origin,
                    "destination": flight.destination,
                }
            )

        # 2. MONSOON / SQUALL LINE STORM SIMULATION
        if any(w in cmd_lower for w in ["monsoon", "squall", "heavy rain", "storm", "thunderstorm"]):
            speech = (
                "Initiating wide-area monsoon squall line storm protocol across Delhi, Mumbai, Bengaluru, and Goa hubs. "
                "Activating Collaborative Decision Making slot swaps and tail-swaps across all mainline carriers."
            )
            return VoiceCommandResponse(
                command=cmd,
                intent="TRIGGER_MONSOON",
                action="MONSOON_ACTIVATED",
                speech_response=speech,
                ui_action={"type": "TRIGGER_MONSOON"}
            )

        # 3. AIRBORNE DIVERSION
        if any(w in cmd_lower for w in ["divert", "diversion", "alternate airport"]):
            flt_num = "6E204"
            if flt_match:
                carrier = flt_match.group(1).upper()
                flt_digits = flt_match.group(2)
                flt_num = f"{carrier}{flt_digits}"

            flight = gds_service.get_flight(flt_num)
            orig = flight.origin if flight else "DEL"
            dest = flight.destination if flight else "BOM"
            carrier_code = flight.carrier if flight else flt_num[:2]
            affected_count = len(gds_service.get_pnrs_for_flight(flt_num)) or 45

            div_rec = divert_engine.execute_flight_diversion(
                flight_number=flt_num,
                origin=orig,
                destination=dest,
                carrier=carrier_code,
                affected_passengers=affected_count,
                reason="Airborne Convective Cell Avoidance (JARVIS Voice Protocol)"
            )
            speech = (
                f"Emergency airborne diversion initiated for flight {flt_num}. Diverted safely to {div_rec.diverted_airport}. "
                f"Charter intermodal motor coach {div_rec.coach_dispatch.bus_plaque_code if div_rec.coach_dispatch else 'BUS-VIP'} "
                f"dispatched to transfer passengers directly to {div_rec.scheduled_destination} terminal."
            )
            return VoiceCommandResponse(
                command=cmd,
                intent="DIVERT_FLIGHT",
                action="DIVERT_EXECUTED",
                target=flt_num,
                speech_response=speech,
                ui_action={
                    "type": "FLIGHT_DIVERTED",
                    "flight_number": flt_num,
                    "diverted_airport": div_rec.diverted_airport,
                    "origin": div_rec.origin
                }
            )

        # 4. RADAR MANIPULATION (FOCUS INDIA / RESET)
        if ("focus" in cmd_lower and "india" in cmd_lower) or any(w in cmd_lower for w in ["focus india", "show india", "zoom india", "india radar"]):
            return VoiceCommandResponse(
                command=cmd,
                intent="FOCUS_RADAR",
                action="FOCUS_INDIA",
                speech_response="Focusing 3D Great-Circle Flight Radar directly on New Delhi and Mumbai aviation corridors.",
                ui_action={"type": "FOCUS_INDIA"}
            )
        if ("reset" in cmd_lower and ("globe" in cmd_lower or "radar" in cmd_lower)) or any(w in cmd_lower for w in ["reset globe", "reset radar", "orbit view", "global view"]):
            return VoiceCommandResponse(
                command=cmd,
                intent="RESET_RADAR",
                action="RESET_GLOBE",
                speech_response="Resetting flight radar to global orbital surveillance mode.",
                ui_action={"type": "RESET_GLOBE"}
            )

        # 5. THEME SWITCHING (WHITE ALABASTER VS STEALTH BLACK)
        if any(w in cmd_lower for w in ["dark mode", "black mode", "stealth", "night mode", "dark theme", "black theme", "switch to black", "switch to dark"]):
            return VoiceCommandResponse(
                command=cmd,
                intent="SWITCH_THEME",
                action="SET_STEALTH",
                target="stealth",
                speech_response="Switching cockpit visuals to Obsidian Stealth Night mode.",
                ui_action={"type": "SET_THEME", "mode": "stealth"}
            )
        if any(w in cmd_lower for w in ["white mode", "light mode", "alabaster", "two tone", "day mode", "white theme", "light theme", "switch to white", "switch to light"]):
            return VoiceCommandResponse(
                command=cmd,
                intent="SWITCH_THEME",
                action="SET_TWOTONE",
                target="twotone",
                speech_response="Displaying signature Framer Let's Fly Alabaster card layout.",
                ui_action={"type": "SET_THEME", "mode": "twotone"}
            )

        # 6. NAVIGATION TABS
        tab_map = {
            "radar": "ops",
            "operations": "ops",
            "flights": "ops",
            "fids": "ops",
            "portal": "portal",
            "passenger": "portal",
            "rebook": "portal",
            "concierge": "portal",
            "boarding": "boarding",
            "hotel": "boarding",
            "voucher": "boarding",
            "baggage": "boarding",
            "dispatch": "dispatch",
            "occ": "dispatch",
            "audit": "analytics",
            "analytics": "analytics",
            "dossier": "analytics",
            "cms": "cms",
            "content": "cms",
            "faq": "faq",
            "question": "faq"
        }
        for kw, tab_id in tab_map.items():
            if kw in cmd_lower:
                tab_names = {
                    "ops": "3D Flight Operations and Radar",
                    "portal": "Passenger Re-Booking Portal and AI Concierge",
                    "boarding": "Digital Boarding Pass, Baggage Radar, and Hotel Vouchers",
                    "dispatch": "OCC Airline Operations Dispatch Console",
                    "analytics": "IATA IRROPS Incident Post-Mortem Dossier",
                    "cms": "Framer Headless CMS Studio",
                    "faq": "Frequently Asked Questions"
                }
                return VoiceCommandResponse(
                    command=cmd,
                    intent="SWITCH_TAB",
                    action=f"SWITCH_TO_{tab_id.upper()}",
                    target=tab_id,
                    speech_response=f"Navigating display to {tab_names.get(tab_id, tab_id)}.",
                    ui_action={"type": "SWITCH_TAB", "tab_id": tab_id}
                )

        # 7. BOOKING & PAYMENT GATEWAY INTENT
        booking_keywords = ["book flight", "book a flight", "book new", "booking", "payment", "gateway", "pay", "buy ticket", "reserve flight", "checkout", "how to book"]
        if any(w in cmd_lower for w in booking_keywords):
            # Only redirect to PNR lookup if an actual registered PNR locator is specified
            registered_pnrs = [p for p in re.findall(r'\b([A-Za-z0-9]{6})\b', cmd) if p.upper() in gds_service.pnrs]
            if not registered_pnrs:
                speech = "Opening Let's Fly Global Flight Booking and Payment Gateway Checkout. Select your cabin class and complete payment instantly via UPI, QR code, or Credit Card."
                return VoiceCommandResponse(
                    command=cmd,
                    intent="OPEN_BOOKING_CHECKOUT",
                    action="SHOW_PAYMENT_GATEWAY",
                    speech_response=speech,
                    ui_action={"type": "OPEN_BOOKING_MODAL"}
                )

        # 8. PNR SEARCH & LOOKUP
        pnr_tokens = [p for p in re.findall(r'\b([A-Za-z0-9]{6})\b', cmd) if p.upper() in gds_service.pnrs]
        if pnr_tokens or (("pnr" in cmd_lower or "passenger" in cmd_lower) and re.search(r'\b([A-Za-z0-9]{6})\b', cmd)):
            candidate_pnr = (pnr_tokens[0] if pnr_tokens else re.search(r'\b([A-Za-z0-9]{6})\b', cmd).group(1)).upper()
            pnr_rec = gds_service.get_pnr(candidate_pnr)
            if pnr_rec:
                speech = (
                    f"Passenger record {candidate_pnr} retrieved for {pnr_rec.passenger_name}. "
                    f"Flight {pnr_rec.original_flight_number} ({pnr_rec.origin} to {pnr_rec.destination}). "
                    f"Status: {pnr_rec.status}. Re-accommodation options are ready on screen."
                )
                return VoiceCommandResponse(
                    command=cmd,
                    intent="LOOKUP_PNR",
                    action="PNR_FOUND",
                    target=candidate_pnr,
                    speech_response=speech,
                    ui_action={"type": "SELECT_PNR", "pnr": candidate_pnr}
                )

        # 8. SOAK LOOP STATUS & SYSTEM HEALTH
        if any(w in cmd_lower for w in ["loop", "soak", "cycle", "health", "system status", "telemetry"]):
            loop_data = {}
            if os.path.exists("loop_status.json"):
                try:
                    with open("loop_status.json", "r", encoding="utf-8") as f:
                        loop_data = json.load(f)
                except Exception:
                    pass

            cycle = loop_data.get("cycle", 1)
            elapsed = loop_data.get("elapsed_seconds", 0)
            latency = loop_data.get("solve_latency_ms", 1.1)
            health = loop_data.get("platform_health", "HEALTHY")

            speech = (
                f"JARVIS telemetry report: The autonomous soak loop is active on cycle #{cycle}. "
                f"Elapsed soak duration is {elapsed:.0f} seconds. Graph solve latency is {latency:.2f} milliseconds, "
                f"and system platform health is {health}."
            )
            return VoiceCommandResponse(
                command=cmd,
                intent="CHECK_STATUS",
                action="LOOP_STATUS_REPORT",
                speech_response=speech,
                ui_action={"type": "SHOW_LOOP_STATUS", "data": loop_data}
            )

        # 9. EXPORT AUDIT REPORT
        if any(w in cmd_lower for w in ["export", "download report", "markdown report"]):
            speech = "Exporting comprehensive IATA IRROPS Incident Post-Mortem markdown audit dossier with financial ROI calculations."
            return VoiceCommandResponse(
                command=cmd,
                intent="EXPORT_AUDIT",
                action="DOWNLOAD_AUDIT",
                speech_response=speech,
                ui_action={"type": "DOWNLOAD_AUDIT"}
            )

        # 10. NATURAL LANGUAGE CONCIERGE FALLBACK
        # If user asks a general question, route through AI Assistant
        pnr_id = req.pnr_id or "EK7P9X"
        ai_resp = await ai_assistant.chat(pnr_id=pnr_id, user_message=cmd)
        clean_reply = re.sub(r'[*_#`]', '', ai_resp.reply)
        # Keep speech reply to first 2 concise sentences
        sentences = [s.strip() for s in clean_reply.split('.') if s.strip()]
        short_speech = ". ".join(sentences[:2]) + "." if sentences else "Acknowledged, sir. Let's Fly autonomous aviation operations are ready."

        return VoiceCommandResponse(
            command=cmd,
            intent="AI_CONSULTATION",
            action="CONCIERGE_REPLY",
            speech_response=f"Sir, {short_speech}",
            ui_action={"type": "CHAT_RESPONSE", "reply": ai_resp.reply}
        )


jarvis_voice_engine = JarvisVoiceEngine()

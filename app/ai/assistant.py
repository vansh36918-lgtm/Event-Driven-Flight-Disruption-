"""
Automated Airline Operations Dispatch & Re-Ticketing Console.
Provides concise, high-density terminal-grade flight status, disruption mitigation,
and autonomous re-accommodation execution following standard IATA/GDS communication formats.
"""
import os
import re
from typing import Dict, Any, Optional
from app.engine.gds_service import gds_service
from app.models.schemas import ChatMessageResponse, PassengerRecord


class AIAssistant:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def _format_option_summary(self, opt: Dict[str, Any], index: int) -> str:
        route_type = opt.get("route_type", "DIRECT")
        segments = opt.get("segments", [])
        total_dur = opt.get("total_duration_minutes", 0)
        delay_min = opt.get("departure_delay_minutes", 0)
        dur_str = f"{total_dur // 60}h {total_dur % 60:02d}m"

        if route_type == "DIRECT" and segments:
            seg = segments[0]
            dep = seg.get("departure_time", "")[11:16]
            arr = seg.get("arrival_time", "")[11:16]
            return (
                f"[{index}] DIRECT {seg.get('flight_number')} | "
                f"DEP {dep} UTC -> ARR {arr} UTC | "
                f"DELAY +{delay_min}m | FLIGHT TIME {dur_str}"
            )
        else:
            legs = " -> ".join([s.get("flight_number", "") for s in segments])
            via = "/".join(opt.get("layover_airports", []))
            dep = opt.get("departure_time", "")[11:16]
            arr = opt.get("arrival_time", "")[11:16]
            return (
                f"[{index}] 1-STOP {legs} (VIA {via}) | "
                f"DEP {dep} UTC -> ARR {arr} UTC | "
                f"DELAY +{delay_min}m | TOTAL TRAVEL {dur_str}"
            )

    async def chat(self, pnr_id: str, user_message: str) -> ChatMessageResponse:
        """Processes dispatch and passenger requests with clean, concise airline operational status."""
        pnr: Optional[PassengerRecord] = gds_service.get_pnr(pnr_id)
        if not pnr:
            return ChatMessageResponse(
                reply=f"ERR-404: PNR record '{pnr_id}' not found in active GDS partition.",
                pnr_id=pnr_id,
                detected_intent="UNKNOWN_PNR",
            )

        msg_lower = user_message.lower().strip()

        # Intent 1: Lock in / Confirm Re-ticketing
        option_match = re.search(r"(?:option|choice|pick|select|rebook|confirm|opt)\s*(?:#|number)?\s*([1-3])", msg_lower)
        if not option_match and ("yes" in msg_lower or "first" in msg_lower or "earliest" in msg_lower or "confirm" in msg_lower):
            if pnr.reaccommodation_options and pnr.status == "DISRUPTED":
                option_match = re.search(r"(\d)", "1")

        if option_match and pnr.reaccommodation_options:
            choice_idx = int(option_match.group(1)) - 1
            if 0 <= choice_idx < len(pnr.reaccommodation_options):
                chosen_opt = pnr.reaccommodation_options[choice_idx]
                opt_id = chosen_opt.get("option_id")
                updated_pnr = gds_service.confirm_pnr_rebook(pnr_id, opt_id)

                segments = chosen_opt.get("segments", [])
                flight_summary = " + ".join([s.get("flight_number") for s in segments])
                dep_utc = chosen_opt.get("departure_time", "")[11:16]
                arr_utc = chosen_opt.get("arrival_time", "")[11:16]

                reply = (
                    f"**[RE-ACCOMMODATION CONFIRMED]**\n\n"
                    f"RECORD LOCATOR: `{pnr.pnr_id}`\n"
                    f"PASSENGER: {pnr.passenger_name}\n"
                    f"NEW FLIGHT: **{flight_summary}** ({pnr.origin} -> {pnr.destination})\n"
                    f"SCHEDULE: DEP {dep_utc} UTC | ARR {arr_utc} UTC\n"
                    f"CLASS: {pnr.fare_class.value} (Confirmed) | STATUS: TICKETED\n"
                    f"BAGGAGE: Auto-rerouted to destination carousel\n"
                    f"E-TICKET: Dispatched to `{pnr.email}`"
                )
                return ChatMessageResponse(
                    reply=reply,
                    pnr_id=pnr_id,
                    detected_intent="CONFIRM_REBOOK",
                    action_taken=f"REBOOKED_{opt_id}",
                    suggested_options=None,
                )

        # Intent 2: Inquiring about disruption / options
        if pnr.status == "DISRUPTED":
            if pnr.reaccommodation_options:
                lines = [self._format_option_summary(opt, i + 1) for i, opt in enumerate(pnr.reaccommodation_options)]
                options_block = "\n".join(lines)
                cta = "\n\nReply with **'Option 1'**, **'Option 2'**, or **'Confirm'** to issue new boarding documents."
            else:
                options_block = "Constrained graph solver calculating alternative routing vectors."
                cta = " Stand by for automatic queue dispatch."

            reply = (
                f"**DISRUPTION NOTICE — FLIGHT {pnr.original_flight_number}**\n"
                f"ROUTING: {pnr.origin} -> {pnr.destination} | PASSENGER: {pnr.passenger_name} (`{pnr.pnr_id}`)\n"
                f"STATUS: CANCELLED (IATA Code 89 - Operational Equipment)\n\n"
                f"**Autonomous Alternatives (4-Hour Window):**\n"
                f"{options_block}"
                f"{cta}"
            )
            return ChatMessageResponse(
                reply=reply,
                pnr_id=pnr_id,
                detected_intent="DISRUPTION_INQUIRY",
                suggested_options=pnr.reaccommodation_options,
            )

        elif pnr.status == "RE_ACCOMMODATED":
            reply = (
                f"**RE-TICKETED ITINERARY CONFIRMED**\n"
                f"RECORD: `{pnr.pnr_id}` | PASSENGER: {pnr.passenger_name}\n"
                f"ASSIGNED ROUTE: `{pnr.selected_option_id}`\n"
                f"STATUS: CHECKED-IN / READY FOR BOARDING"
            )
            return ChatMessageResponse(
                reply=reply,
                pnr_id=pnr_id,
                detected_intent="ALREADY_REACCOMMODATED",
            )
        else:
            reply = (
                f"**FLIGHT STATUS NORMAL**\n"
                f"FLIGHT: {pnr.original_flight_number} ({pnr.origin} -> {pnr.destination})\n"
                f"RECORD: `{pnr.pnr_id}` | PASSENGER: {pnr.passenger_name}\n"
                f"STATUS: ON TIME / SCHEDULED\n"
                f"Baggage drop and gate check open 2h prior to departure."
            )
            return ChatMessageResponse(
                reply=reply,
                pnr_id=pnr_id,
                detected_intent="SCHEDULE_NORMAL",
            )


# Singleton assistant
ai_assistant = AIAssistant()

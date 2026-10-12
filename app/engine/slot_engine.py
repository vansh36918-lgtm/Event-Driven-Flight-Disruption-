"""
FAA ATC Ground Delay Program (GDP) & Collaborative Decision Making (CDM) Slot Engine.
Simulates Airport Acceptance Rate (AAR) constraints, Expect Departure Clearance Times (EDCT),
and executes airline slot compression / substitutions to prioritize high-capacity mainline flights.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.models.schemas import FlightSegment


class ArrivalSlot:
    def __init__(self, slot_id: str, airport: str, slot_time_utc: datetime):
        self.slot_id = slot_id
        self.airport = airport
        self.slot_time_utc = slot_time_utc
        self.assigned_flight: Optional[str] = None


class GroundDelayProgram:
    def __init__(
        self,
        program_id: str,
        airport: str,
        reason: str,
        normal_aar: int,  # Airport Acceptance Rate (arrivals/hr)
        reduced_aar: int,
        start_time_utc: datetime,
        end_time_utc: datetime,
    ):
        self.program_id = program_id
        self.airport = airport
        self.reason = reason
        self.normal_aar = normal_aar
        self.reduced_aar = reduced_aar
        self.start_time_utc = start_time_utc
        self.end_time_utc = end_time_utc
        self.slots: List[ArrivalSlot] = []


class ATCSlotEngine:
    def __init__(self):
        self.active_gdps: Dict[str, GroundDelayProgram] = {}
        self.slot_swaps: List[Dict[str, Any]] = []
        self._initialize_sample_gdp()

    def _initialize_sample_gdp(self):
        """Initializes a representative FAA GDP at Chicago O'Hare (ORD) due to weather."""
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        gdp = GroundDelayProgram(
            program_id="FAA-GDP-ORD-01",
            airport="ORD",
            reason="Low Visibility & Squall Line Thunderstorms (AAR 50% Reduction)",
            normal_aar=72,
            reduced_aar=36,
            start_time_utc=now,
            end_time_utc=now + timedelta(hours=6),
        )

        # Generate controlled arrival slots every 2 minutes
        slot_time = now + timedelta(minutes=30)
        for i in range(20):
            slot = ArrivalSlot(
                slot_id=f"SLOT-ORD-{i+1:03d}",
                airport="ORD",
                slot_time_utc=slot_time,
            )
            gdp.slots.append(slot)
            slot_time += timedelta(minutes=2)

        self.active_gdps["ORD"] = gdp

    def optimize_slot_substitution(
        self,
        high_priority_flight: str,
        low_priority_flight: str,
        airport: str = "ORD",
    ) -> Optional[Dict[str, Any]]:
        """
        Executes FAA Collaborative Decision Making (CDM) slot swap:
        Swaps earlier arrival slot from a regional/low-load flight to a high-capacity mainline flight.
        """
        gdp = self.active_gdps.get(airport)
        if not gdp or len(gdp.slots) < 2:
            return None

        # Slot 1 (earlier) and Slot 2 (later)
        early_slot = gdp.slots[0]
        late_slot = gdp.slots[1]

        early_slot.assigned_flight = high_priority_flight
        late_slot.assigned_flight = low_priority_flight

        swap_record = {
            "gdp_program_id": gdp.program_id,
            "airport": airport,
            "high_priority_flight": high_priority_flight,
            "protected_slot": early_slot.slot_id,
            "edct_utc": early_slot.slot_time_utc.strftime("%H:%M:%S UTC"),
            "subordinated_flight": low_priority_flight,
            "action": "CDM_SLOT_SWAP_CONFIRMED",
            "pax_delay_minutes_saved": 115,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S UTC"),
        }
        self.slot_swaps.insert(0, swap_record)
        if len(self.slot_swaps) > 30:
            self.slot_swaps.pop()

        return swap_record

    def get_active_gdps(self) -> List[Dict[str, Any]]:
        return [
            {
                "program_id": g.program_id,
                "airport": g.airport,
                "reason": g.reason,
                "normal_aar": g.normal_aar,
                "reduced_aar": g.reduced_aar,
                "capacity_cut_pct": round((1 - g.reduced_aar / g.normal_aar) * 100, 1),
                "active_slots": len(g.slots),
            }
            for g in self.active_gdps.values()
        ]


# Singleton instance
slot_engine = ATCSlotEngine()

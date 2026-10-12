"""
FAA FAR Part 117 / Part 121 Crew Pairing & Cascading Disruption Engine.
Tracks pilot and flight attendant legal duty periods (FDP), rest rules,
and detects downstream crew timeouts when antecedent flights are delayed or grounded.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from app.models.schemas import FlightSegment


class CrewPairing:
    def __init__(
        self,
        pairing_id: str,
        crew_type: str,  # "FLIGHT_CREW" (Pilots) or "CABIN_CREW"
        duty_start_utc: datetime,
        max_fdp_hours: float = 14.0,  # FAA Part 117 Max Flight Duty Period
        min_rest_hours: float = 10.0,
    ):
        self.pairing_id = pairing_id
        self.crew_type = crew_type
        self.duty_start_utc = duty_start_utc
        self.max_fdp_hours = max_fdp_hours
        self.min_rest_hours = min_rest_hours
        self.assigned_flights: List[str] = []  # List of flight numbers in sequence

    @property
    def hard_timeout_utc(self) -> datetime:
        return self.duty_start_utc + timedelta(hours=self.max_fdp_hours)


class CrewDisruptionEngine:
    def __init__(self):
        self.pairings: Dict[str, CrewPairing] = {}
        self.flight_to_pairing: Dict[str, str] = {}
        self._initialize_crew_rotations()

    def _initialize_crew_rotations(self):
        """Initializes realistic multi-leg crew pairings linked to hub flight rotations."""
        base_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Pre-assign standard multi-leg rotations nearing statutory FDP limits
        rotations = [
            ("CP-101", ["AA100", "AA101", "AA102"], base_time - timedelta(hours=10.0)),
            ("CP-102", ["DL100", "DL101", "DL102"], base_time - timedelta(hours=10.5)),
            ("CP-103", ["UA100", "UA101", "UA102"], base_time - timedelta(hours=9.5)),
            ("CP-104", ["B6100", "B6101", "B6102"], base_time - timedelta(hours=11.0)),
        ]

        for pid, flights, start_time in rotations:
            pairing = CrewPairing(
                pairing_id=pid,
                crew_type="FLIGHT_CREW",
                duty_start_utc=start_time,
                max_fdp_hours=13.0,  # 13 hours allowable for multi-segment duty
            )
            pairing.assigned_flights = flights
            self.pairings[pid] = pairing
            for f_num in flights:
                self.flight_to_pairing[f_num] = pid

    def evaluate_cascading_timeout(
        self, disrupted_flight_number: str, delay_minutes: int = 180
    ) -> List[Dict[str, Any]]:
        """
        Evaluates whether a delay on the antecedent flight triggers an illegal
        FAA Part 117 Flight Duty Period (FDP) breach on downstream assigned flight legs.
        Returns a list of cascading secondary disruption alerts.
        """
        pairing_id = self.flight_to_pairing.get(disrupted_flight_number)
        if not pairing_id or pairing_id not in self.pairings:
            return []

        pairing = self.pairings[pairing_id]
        cascading_alerts = []

        try:
            curr_idx = pairing.assigned_flights.index(disrupted_flight_number)
        except ValueError:
            return []

        downstream_legs = pairing.assigned_flights[curr_idx + 1 :]
        accumulated_delay = timedelta(minutes=delay_minutes)

        # Estimate impact on each subsequent flight in the rotation
        for leg in downstream_legs:
            estimated_duty_needed = timedelta(hours=2.5)  # 2.5h average flight block
            projected_duty_end = datetime.utcnow() + accumulated_delay + estimated_duty_needed

            if projected_duty_end > pairing.hard_timeout_utc:
                timeout_minutes = int((projected_duty_end - pairing.hard_timeout_utc).total_seconds() / 60)
                alert = {
                    "cascading_flight_number": leg,
                    "pairing_id": pairing.pairing_id,
                    "antecedent_flight": disrupted_flight_number,
                    "reason": f"FAA Part 117 FDP Timeout (+{timeout_minutes}m duty breach)",
                    "action_required": "CREW_SWAP_OR_GROUND",
                    "duty_start": pairing.duty_start_utc.isoformat(),
                    "hard_timeout_utc": pairing.hard_timeout_utc.isoformat(),
                    "projected_duty_end": projected_duty_end.isoformat(),
                }
                cascading_alerts.append(alert)

        return cascading_alerts


# Singleton instance
crew_engine = CrewDisruptionEngine()

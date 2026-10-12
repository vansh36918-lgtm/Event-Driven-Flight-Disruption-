"""
Aircraft Fleet Tracking & Tail-Swap Recovery Engine.
Simulates physical aircraft registration numbers (e.g., N101AA, N402DL),
turnaround times, hub maintenance bases, and resolves aircraft shortage
via operational tail-swaps during irregular operations (IRROPS).
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.models.schemas import FlightSegment


class AircraftTail:
    def __init__(self, tail_number: str, model: str, carrier: str, current_airport: str):
        self.tail_number = tail_number
        self.model = model  # B737-800, A321neo, B777-200
        self.carrier = carrier
        self.current_airport = current_airport
        self.scheduled_flights: List[str] = []
        self.is_grounded: bool = False
        self.available_after_utc: datetime = datetime.utcnow()


class FleetRecoveryEngine:
    def __init__(self):
        self.fleet: Dict[str, AircraftTail] = {}
        self.flight_to_tail: Dict[str, str] = {}
        self.tail_swap_history: List[Dict[str, Any]] = []
        self._initialize_fleet()

    def _initialize_fleet(self):
        """Initializes hub fleet allocations across major US bases."""
        hubs = ["JFK", "ORD", "LAX", "DFW", "ATL", "SFO", "MIA", "DEN", "BOS", "SEA"]
        carriers = ["AA", "DL", "UA", "B6"]
        models = ["B737-800", "A321neo", "A320", "B777-200"]

        tail_id = 101
        for carrier in carriers:
            for hub in hubs:
                # 2-3 aircraft based per hub per carrier
                for _ in range(2):
                    reg = f"N{tail_id}{carrier}"
                    tail_id += 1
                    tail = AircraftTail(
                        tail_number=reg,
                        model=random.choice(models),
                        carrier=carrier,
                        current_airport=hub,
                    )
                    self.fleet[reg] = tail

    def assign_tail_to_flight(self, flight: FlightSegment) -> str:
        """Assigns an available aircraft tail matching carrier and origin."""
        carrier = flight.carrier
        origin = flight.origin

        # Find matching tail at origin
        candidates = [
            t for t in self.fleet.values()
            if t.carrier == carrier and t.current_airport == origin and not t.is_grounded
        ]

        if candidates:
            tail = candidates[0]
        else:
            # Fallback to any spare tail
            tail = list(self.fleet.values())[0]

        tail.scheduled_flights.append(flight.flight_number)
        self.flight_to_tail[flight.flight_number] = tail.tail_number
        return tail.tail_number

    def evaluate_tail_swap(
        self, disrupted_flight_number: str, origin: str, carrier: str
    ) -> Optional[Dict[str, Any]]:
        """
        When a flight is grounded or delayed, checks if a tail-swap with a spare
        aircraft or a lower-priority turnaround flight can salvage operations.
        """
        # Find spare aircraft of the same carrier stationed at origin
        spares = [
            t for t in self.fleet.values()
            if t.carrier == carrier and t.current_airport == origin and not t.is_grounded
            and len(t.scheduled_flights) <= 1
        ]

        if spares:
            spare_tail = spares[0]
            current_tail_num = self.flight_to_tail.get(disrupted_flight_number, "UNASSIGNED")
            
            swap_record = {
                "disrupted_flight": disrupted_flight_number,
                "original_tail": current_tail_num,
                "assigned_spare_tail": spare_tail.tail_number,
                "aircraft_model": spare_tail.model,
                "hub": origin,
                "action": "TAIL_SWAP_EXECUTED",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S UTC"),
                "turnaround_minutes_saved": 65,
            }
            self.tail_swap_history.insert(0, swap_record)
            if len(self.tail_swap_history) > 30:
                self.tail_swap_history.pop()

            self.flight_to_tail[disrupted_flight_number] = spare_tail.tail_number
            return swap_record

        return None


# Singleton instance
fleet_engine = FleetRecoveryEngine()

"""
GDS (Global Distribution System) Simulator.
Models airline schedules, PNR bookings, seat inventories, and telemetry webhooks
following Sabre/Amadeus standard formats.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.schemas import (
    FlightSegment,
    FlightStatus,
    PassengerRecord,
    FareClass,
    DisruptionWebhookPayload,
    DisruptionType,
)


class GDSService:
    def __init__(self):
        self.flights: Dict[str, FlightSegment] = {}
        self.pnrs: Dict[str, PassengerRecord] = {}
        self.flight_to_pnrs: Dict[str, List[str]] = {}
        self.disruption_history: List[DisruptionWebhookPayload] = []
        self._seed_gds_inventory()

    def _generate_pnr_id(self) -> str:
        """Generates authentic 6-character uppercase alphanumeric PNR containing letters and digits."""
        letters = random.choices(string.ascii_uppercase, k=3)
        alphanumeric = random.choices(string.ascii_uppercase + string.digits, k=3)
        combined = letters + alphanumeric
        random.shuffle(combined)
        return "".join(combined)

    def _seed_gds_inventory(self):
        """Seeds realistic multi-hub flight network across North America and transatlantic routes."""
        airports = [
            ("JFK", "New York"),
            ("ORD", "Chicago"),
            ("LAX", "Los Angeles"),
            ("DFW", "Dallas/Fort Worth"),
            ("ATL", "Atlanta"),
            ("SFO", "San Francisco"),
            ("MIA", "Miami"),
            ("DEN", "Denver"),
            ("BOS", "Boston"),
            ("SEA", "Seattle"),
        ]

        carriers = [("AA", "American Airlines"), ("DL", "Delta"), ("UA", "United"), ("B6", "JetBlue")]
        base_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)

        # Generate direct and connecting flight schedules across the day
        flight_id_counter = 100
        for origin_code, _ in airports:
            for dest_code, _ in airports:
                if origin_code == dest_code:
                    continue

                # Create 3-4 flights per day for each route with staggered departure times
                for hour_offset in [0, 2, 4, 6, 8, 12]:
                    carrier_code, _ = random.choice(carriers)
                    flight_num = f"{carrier_code}{flight_id_counter}"
                    flight_id_counter += 1

                    dep = base_time + timedelta(hours=hour_offset, minutes=random.choice([0, 15, 30, 45]))
                    # Flight duration heuristic: 90 mins to 360 mins
                    duration_min = random.randint(110, 320)
                    arr = dep + timedelta(minutes=duration_min)

                    flight = FlightSegment(
                        flight_number=flight_num,
                        carrier=carrier_code,
                        origin=origin_code,
                        destination=dest_code,
                        departure_time=dep,
                        arrival_time=arr,
                        duration_minutes=duration_min,
                        seats_available=random.randint(15, 80),
                        aircraft_type=random.choice(["B737-800", "A321neo", "B777-200", "A320"]),
                        status=FlightStatus.SCHEDULED,
                    )
                    self.flights[flight_num] = flight
                    self.flight_to_pnrs[flight_num] = []

        # Generate realistic PNR bookings
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "David", "Emma", "Michael", "Sophia", "Liam", "Olivia", "James", "Elena"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris"]

        # Ensure high-profile flights have passengers for immediate demo
        demo_flights = list(self.flights.keys())[:25]
        for flight_num in demo_flights:
            flight = self.flights[flight_num]
            num_passengers = random.randint(25, 60)

            for _ in range(num_passengers):
                pnr_id = self._generate_pnr_id()
                # Ensure uniqueness
                while pnr_id in self.pnrs:
                    pnr_id = self._generate_pnr_id()

                first = random.choice(first_names)
                last = random.choice(last_names)
                pnr = PassengerRecord(
                    pnr_id=pnr_id,
                    passenger_name=f"{first} {last}",
                    email=f"{first.lower()}.{last.lower()}@example.com",
                    phone=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    fare_class=random.choice([FareClass.ECONOMY, FareClass.ECONOMY, FareClass.BUSINESS, FareClass.PREMIUM_ECONOMY]),
                    original_flight_number=flight_num,
                    origin=flight.origin,
                    destination=flight.destination,
                    status="CONFIRMED",
                )
                self.pnrs[pnr_id] = pnr
                self.flight_to_pnrs[flight_num].append(pnr_id)

    def get_flight(self, flight_number: str) -> Optional[FlightSegment]:
        return self.flights.get(flight_number)

    def list_flights(self, limit: int = 50) -> List[FlightSegment]:
        return list(self.flights.values())[:limit]

    def get_pnr(self, pnr_id: str) -> Optional[PassengerRecord]:
        return self.pnrs.get(pnr_id.upper())

    def get_pnrs_for_flight(self, flight_number: str) -> List[PassengerRecord]:
        pnr_ids = self.flight_to_pnrs.get(flight_number, [])
        return [self.pnrs[pid] for pid in pnr_ids if pid in self.pnrs]

    def update_flight_status(self, flight_number: str, status: FlightStatus) -> bool:
        if flight_number in self.flights:
            self.flights[flight_number].status = status
            return True
        return False

    def update_pnr_reaccommodation(self, pnr_id: str, options: List[Dict]) -> bool:
        pnr = self.pnrs.get(pnr_id)
        if pnr:
            pnr.status = "DISRUPTED"
            pnr.reaccommodation_options = options
            return True
        return False

    def confirm_pnr_rebook(self, pnr_id: str, option_id: str) -> Optional[PassengerRecord]:
        pnr = self.pnrs.get(pnr_id.upper())
        if not pnr:
            return None
        pnr.status = "RE_ACCOMMODATED"
        pnr.selected_option_id = option_id
        return pnr

    def record_disruption(self, payload: DisruptionWebhookPayload):
        self.disruption_history.append(payload)
        self.update_flight_status(payload.flight_number, FlightStatus.CANCELLED if payload.disruption_type == DisruptionType.CANCELLATION else FlightStatus.DELAYED)


# Singleton instance
gds_service = GDSService()

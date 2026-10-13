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
from app.engine.baggage_engine import baggage_engine
from app.engine.hotel_engine import hotel_engine



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
        random.seed(42)
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

        # Seed Pan-India Domestic & International Corridor (IndiGo 6E, Air India AI, Akasa QP, Vistara UK)
        indian_routes = [
            # Delhi <-> Mumbai (Maharashtra)
            ("6E204", "6E", "DEL", "BOM", 0, 130, "A321neo"),
            ("AI803", "AI", "DEL", "BOM", 1, 125, "B787-8"),
            ("UK995", "UK", "DEL", "BOM", 2, 130, "A320neo"),
            ("QP1102", "QP", "DEL", "BOM", 3, 135, "B737 MAX"),
            ("6E505", "6E", "BOM", "DEL", 0, 130, "A320neo"),
            ("AI804", "AI", "BOM", "DEL", 2, 125, "B787-8"),
            # Delhi <-> Bengaluru (Karnataka)
            ("6E712", "6E", "DEL", "BLR", 0, 170, "A321neo"),
            ("AI506", "AI", "DEL", "BLR", 2, 165, "A320neo"),
            ("QP1420", "QP", "BLR", "DEL", 1, 175, "B737 MAX"),
            ("6E719", "6E", "BLR", "DEL", 3, 170, "A321neo"),
            # Delhi <-> Hyderabad (Telangana)
            ("6E401", "6E", "DEL", "HYD", 1, 135, "A320neo"),
            ("AI542", "AI", "DEL", "HYD", 2, 130, "A320neo"),
            ("6E406", "6E", "HYD", "DEL", 3, 135, "A320neo"),
            # Delhi <-> Chennai (Tamil Nadu)
            ("6E209", "6E", "DEL", "MAA", 0, 175, "A321neo"),
            ("AI440", "AI", "DEL", "MAA", 2, 170, "A320neo"),
            ("6E212", "6E", "MAA", "DEL", 1, 175, "A321neo"),
            # Delhi <-> Kolkata (West Bengal)
            ("6E214", "6E", "DEL", "CCU", 1, 130, "A320neo"),
            ("AI701", "AI", "DEL", "CCU", 2, 125, "A320neo"),
            ("6E217", "6E", "CCU", "DEL", 3, 130, "A320neo"),
            # Delhi <-> Ahmedabad (Gujarat)
            ("6E125", "6E", "DEL", "AMD", 0, 95, "A320neo"),
            ("AI017", "AI", "DEL", "AMD", 2, 90, "A320neo"),
            ("6E128", "6E", "AMD", "DEL", 1, 95, "A320neo"),
            # Delhi <-> Goa (Goa)
            ("6E611", "6E", "DEL", "GOI", 1, 155, "A321neo"),
            ("AI885", "AI", "DEL", "GOI", 3, 150, "A320neo"),
            ("6E614", "6E", "GOI", "DEL", 2, 155, "A321neo"),
            # Delhi <-> Jaipur (Rajasthan)
            ("6E745", "6E", "DEL", "JAI", 0, 55, "ATR-72"),
            ("AI491", "AI", "DEL", "JAI", 2, 50, "A320neo"),
            ("6E748", "6E", "JAI", "DEL", 1, 55, "ATR-72"),
            # Delhi <-> Lucknow (Uttar Pradesh)
            ("6E2012", "6E", "DEL", "LKO", 0, 65, "A320neo"),
            ("AI431", "AI", "DEL", "LKO", 2, 60, "A320neo"),
            ("6E2015", "6E", "LKO", "DEL", 1, 65, "A320neo"),
            # Delhi <-> Chandigarh (Punjab/Haryana)
            ("6E2112", "6E", "DEL", "IXC", 0, 55, "ATR-72"),
            ("AI463", "AI", "DEL", "IXC", 2, 50, "A320neo"),
            # Delhi <-> Srinagar (Jammu & Kashmir)
            ("6E2021", "6E", "DEL", "SXR", 1, 95, "A320neo"),
            ("AI825", "AI", "DEL", "SXR", 2, 90, "A320neo"),
            ("UK611", "UK", "DEL", "SXR", 3, 95, "A320neo"),
            # Delhi <-> Kochi (Kerala)
            ("6E2101", "6E", "DEL", "COK", 0, 195, "A321neo"),
            ("AI512", "AI", "DEL", "COK", 2, 190, "A320neo"),
            # Delhi <-> Guwahati (Assam / North East)
            ("6E6351", "6E", "DEL", "GAU", 1, 145, "A320neo"),
            ("AI729", "AI", "DEL", "GAU", 2, 140, "A320neo"),
            # Delhi <-> Patna (Bihar)
            ("6E2191", "6E", "DEL", "PAT", 0, 100, "A320neo"),
            ("AI409", "AI", "DEL", "PAT", 2, 95, "A320neo"),
            # Delhi <-> Varanasi (Uttar Pradesh)
            ("6E2201", "6E", "DEL", "VNS", 1, 85, "A320neo"),
            ("AI405", "AI", "DEL", "VNS", 3, 80, "A320neo"),
            # Delhi <-> Bhubaneswar (Odisha)
            ("6E2071", "6E", "DEL", "BBI", 1, 125, "A320neo"),
            ("AI477", "AI", "DEL", "BBI", 2, 120, "A320neo"),
            # Delhi <-> Indore (Madhya Pradesh)
            ("6E2431", "6E", "DEL", "IDR", 0, 85, "A320neo"),
            ("AI635", "AI", "DEL", "IDR", 2, 80, "A320neo"),
            # Delhi <-> Amritsar (Punjab)
            ("6E2145", "6E", "DEL", "ATQ", 1, 65, "A320neo"),
            ("AI453", "AI", "DEL", "ATQ", 2, 60, "A320neo"),
            # Mumbai <-> Bengaluru
            ("6E455", "6E", "BOM", "BLR", 0, 100, "A320neo"),
            ("AI609", "AI", "BOM", "BLR", 2, 95, "A320neo"),
            ("QP1312", "QP", "BOM", "BLR", 3, 100, "B737 MAX"),
            # Mumbai <-> Goa
            ("6E331", "6E", "BOM", "GOI", 0, 75, "A320neo"),
            ("AI685", "AI", "BOM", "GOI", 2, 70, "A320neo"),
            ("QP1512", "QP", "BOM", "GOI", 1, 75, "B737 MAX"),
            ("6E334", "6E", "GOI", "BOM", 3, 75, "A320neo"),
            # Mumbai <-> Hyderabad
            ("6E533", "6E", "BOM", "HYD", 1, 85, "A320neo"),
            ("AI617", "AI", "BOM", "HYD", 2, 80, "A320neo"),
            # Mumbai <-> Chennai
            ("6E671", "6E", "BOM", "MAA", 0, 115, "A320neo"),
            ("AI671", "AI", "BOM", "MAA", 2, 110, "A320neo"),
            # Mumbai <-> Kolkata
            ("6E822", "6E", "BOM", "CCU", 1, 150, "A320neo"),
            ("AI773", "AI", "BOM", "CCU", 3, 145, "A320neo"),
            # Mumbai <-> Ahmedabad
            ("6E5311", "6E", "BOM", "AMD", 0, 70, "A320neo"),
            ("AI019", "AI", "BOM", "AMD", 2, 65, "A320neo"),
            # Mumbai <-> Kochi
            ("6E5101", "6E", "BOM", "COK", 1, 115, "A320neo"),
            ("AI681", "AI", "BOM", "COK", 3, 110, "A320neo"),
            # Mumbai <-> Jaipur
            ("6E5211", "6E", "BOM", "JAI", 0, 105, "A320neo"),
            ("AI611", "AI", "BOM", "JAI", 2, 100, "A320neo"),
            # Bengaluru <-> Hyderabad & Chennai & Goa & Kochi
            ("6E419", "6E", "BLR", "HYD", 0, 65, "A320neo"),
            ("6E391", "6E", "BLR", "MAA", 1, 55, "A320neo"),
            ("6E711", "6E", "BLR", "GOI", 2, 70, "A320neo"),
            ("6E411", "6E", "BLR", "COK", 1, 60, "A320neo"),
            # Kolkata <-> Guwahati & Bagdogra
            ("6E281", "6E", "CCU", "GAU", 0, 65, "A320neo"),
            ("6E291", "6E", "CCU", "IXB", 1, 60, "A320neo"),
            # International Connectors
            ("6E903", "6E", "BOM", "DXB", 1, 210, "A321neo"),
            ("6E1451", "6E", "DEL", "DXB", 2, 235, "A321neo"),
            ("6E1011", "6E", "DEL", "SIN", 0, 335, "A321neo"),
            ("AI101", "AI", "DEL", "JFK", 0, 920, "B777-300ER"),
            ("AI161", "AI", "DEL", "LHR", 1, 570, "B787-8"),
        ]
        for f_num, carrier, orig, dest, hr_off, dur, ac in indian_routes:
            dep = base_time + timedelta(hours=hr_off, minutes=15)
            arr = dep + timedelta(minutes=dur)
            flt = FlightSegment(
                flight_number=f_num,
                carrier=carrier,
                origin=orig,
                destination=dest,
                departure_time=dep,
                arrival_time=arr,
                duration_minutes=dur,
                seats_available=random.randint(20, 95),
                aircraft_type=ac,
                status=FlightStatus.SCHEDULED,
            )
            self.flights[f_num] = flt
            self.flight_to_pnrs[f_num] = []

        # Generate realistic PNR bookings
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "David", "Emma", "Michael", "Sophia", "Liam", "Olivia", "James", "Elena", "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Aditya"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "Sharma", "Verma", "Patel", "Reddy", "Gupta", "Nair", "Iyer"]

        # Ensure high-profile flights have passengers for immediate demo
        demo_flights = list(self.flights.keys())[:25] + [f[0] for f in indian_routes]
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
                fare = random.choice([FareClass.ECONOMY, FareClass.ECONOMY, FareClass.BUSINESS, FareClass.PREMIUM_ECONOMY])
                tier = random.choices(["DIAMOND", "PLATINUM", "GOLD", "SILVER", "GENERAL"], weights=[5, 10, 20, 25, 40])[0]
                
                # Compute Passenger Value Score (PVS)
                tier_weights = {"DIAMOND": 500, "PLATINUM": 380, "GOLD": 260, "SILVER": 150, "GENERAL": 50}
                class_weights = {FareClass.FIRST: 450, FareClass.BUSINESS: 380, FareClass.PREMIUM_ECONOMY: 220, FareClass.ECONOMY: 100}
                pvs = tier_weights[tier] + class_weights[fare] + random.randint(10, 50)

                pnr = PassengerRecord(
                    pnr_id=pnr_id,
                    passenger_name=f"{first} {last}",
                    email=f"{first.lower()}.{last.lower()}@example.com",
                    phone=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    fare_class=fare,
                    loyalty_tier=tier,
                    pvs_score=pvs,
                    original_flight_number=flight_num,
                    origin=flight.origin,
                    destination=flight.destination,
                    status="CONFIRMED",
                )
                self.pnrs[pnr_id] = pnr
                self.flight_to_pnrs[flight_num].append(pnr_id)

        # Guarantee canonical demo PNRs (including BF6JB7) across all deployments and serverless instances
        canonical_pnrs = [
            ("BF6JB7", "Aarav Sharma", "aarav.sharma@letsfly.aero", "6E204", "DEL", "BOM", "PLATINUM", FareClass.BUSINESS, 480),
            ("HVLHZX", "Chris Williams", "chris.williams@letsfly.aero", "6E204", "DEL", "BOM", "DIAMOND", FareClass.BUSINESS, 520),
            ("AKL2WB", "Priya Patel", "priya.patel@letsfly.aero", "AI803", "DEL", "BOM", "GOLD", FareClass.ECONOMY, 350),
            ("LFYHEN", "Jordan Smith", "jordan.smith@letsfly.aero", "6E712", "DEL", "BLR", "PLATINUM", FareClass.BUSINESS, 450),
        ]
        for pid, name, email, flt_no, orig, dest, tier, fare, pvs in canonical_pnrs:
            flt = self.flights.get(flt_no)
            if flt:
                self.pnrs[pid] = PassengerRecord(
                    pnr_id=pid,
                    passenger_name=name,
                    email=email,
                    phone="+91-98112-44550",
                    fare_class=fare,
                    loyalty_tier=tier,
                    pvs_score=pvs,
                    original_flight_number=flt_no,
                    origin=orig,
                    destination=dest,
                    status="CONFIRMED",
                )
                if pid not in self.flight_to_pnrs.setdefault(flt_no, []):
                    self.flight_to_pnrs[flt_no].insert(0, pid)

    def get_flight(self, flight_number: str) -> Optional[FlightSegment]:
        return self.flights.get(flight_number)

    def list_flights(self, limit: int = 50) -> List[FlightSegment]:
        return list(self.flights.values())[:limit]

    def get_pnr(self, pnr_id: str) -> Optional[PassengerRecord]:
        clean_id = pnr_id.strip().upper()
        if clean_id in self.pnrs:
            return self.pnrs[clean_id]

        flight_pnrs = self.get_pnrs_for_flight(clean_id)
        if flight_pnrs:
            return flight_pnrs[0]

        # Resilient Serverless Fallback: If querying any alphanumeric PNR (e.g. BF6JB7 or user booking)
        # auto-synthesize and register a valid passenger record so serverless cold-starts never break.
        if 4 <= len(clean_id) <= 8 and clean_id.isalnum():
            hash_val = sum(ord(c) for c in clean_id)
            target_flight = self.get_flight("6E204") or list(self.flights.values())[0]

            first_names = ["Alex", "Aarav", "Priya", "Rohan", "Elena", "Sam", "Chris", "Neha", "Vikram", "Taylor"]
            last_names = ["Sharma", "Patel", "Verma", "Gupta", "Reddy", "Nair", "Iyer", "Williams", "Johnson", "Smith"]
            first = first_names[hash_val % len(first_names)]
            last = last_names[(hash_val // len(first_names)) % len(last_names)]

            is_disrupted = target_flight.status in (FlightStatus.CANCELLED, FlightStatus.DELAYED)

            auto_pnr = PassengerRecord(
                pnr_id=clean_id,
                passenger_name=f"{first} {last}",
                email=f"{first.lower()}.{last.lower()}@letsfly.aero",
                phone=f"+91-98{hash_val % 10000:04d}-{(hash_val * 7) % 10000:04d}",
                fare_class=FareClass.BUSINESS if hash_val % 3 == 0 else FareClass.ECONOMY,
                loyalty_tier="PLATINUM" if hash_val % 4 == 0 else "GOLD",
                pvs_score=380 + (hash_val % 150),
                original_flight_number=target_flight.flight_number,
                origin=target_flight.origin,
                destination=target_flight.destination,
                status="DISRUPTED" if is_disrupted else "CONFIRMED",
            )

            if is_disrupted:
                try:
                    from app.engine.graph_engine import reaccommodation_engine
                    routes = reaccommodation_engine.find_alternatives(
                        origin=target_flight.origin,
                        destination=target_flight.destination,
                        original_departure=target_flight.departure_time,
                        max_window_hours=4,
                        preferred_carrier=target_flight.carrier,
                    )
                    auto_pnr.reaccommodation_options = [r.model_dump(mode="json") for r in routes]
                except Exception:
                    pass

            self.pnrs[clean_id] = auto_pnr
            if target_flight.flight_number in self.flight_to_pnrs:
                self.flight_to_pnrs[target_flight.flight_number].append(clean_id)
            return auto_pnr

        return None

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

        # IATA Resolution 766 Operational Cabin Upgrade (Op-Up) rule:
        # High-value travelers (DIAMOND / PLATINUM or PVS >= 650) rebooked from Economy receive complimentary Business cabin protection
        if pnr.pvs_score >= 650 or pnr.loyalty_tier in ("DIAMOND", "PLATINUM"):
            if pnr.fare_class in (FareClass.ECONOMY, FareClass.PREMIUM_ECONOMY):
                pnr.upgraded_cabin = "BUSINESS (CLASS J)"
                pnr.upgrade_reason = "IATA RES 766 HIGH-PVS PRIORITY MITIGATION"

        # IATA Resolution 753 Automated Baggage Reroute Order
        new_flight_num = pnr.original_flight_number
        if pnr.reaccommodation_options:
            chosen = next((o for o in pnr.reaccommodation_options if o.get("option_id") == option_id), pnr.reaccommodation_options[0])
            segments = chosen.get("segments", [])
            if segments:
                new_flight_num = segments[0].get("flight_number", new_flight_num)

        baggage_engine.auto_reroute_baggage(pnr.pnr_id, pnr.original_flight_number, new_flight_num, pnr.origin, pnr.destination)

        # Automated CRS/Sabre Hotel Voucher Check (EU261 Article 9 & US DOT overnight mandate)
        dep_time = None
        if pnr.reaccommodation_options:
            chosen = next((o for o in pnr.reaccommodation_options if o.get("option_id") == option_id), pnr.reaccommodation_options[0])
            segments = chosen.get("segments", [])
            if segments:
                dep_time = segments[0].get("departure_time")

        orig_flt = self.flights.get(pnr.original_flight_number)
        orig_sched = orig_flt.departure_time.isoformat() if (orig_flt and hasattr(orig_flt, "departure_time") and orig_flt.departure_time) else ""
        if hotel_engine.is_overnight_delay(orig_sched, dep_time):
            hotel_engine.issue_hotel_voucher(
                pnr_id=pnr.pnr_id,
                passenger_name=pnr.passenger_name,
                disrupted_flight_num=pnr.original_flight_number,
                hub_airport=pnr.origin,
                cabin_class=pnr.fare_class.value if hasattr(pnr.fare_class, "value") else str(pnr.fare_class),
                pvs_score=pnr.pvs_score,
                reaccommodated_flight_num=new_flight_num,
            )

        return pnr



    def record_disruption(self, payload: DisruptionWebhookPayload):
        self.disruption_history.append(payload)
        self.update_flight_status(payload.flight_number, FlightStatus.CANCELLED if payload.disruption_type == DisruptionType.CANCELLATION else FlightStatus.DELAYED)


# Singleton instance
gds_service = GDSService()

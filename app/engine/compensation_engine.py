"""
Passenger Rights, Regulatory Compensation & Voucher Engine.
Implements US DOT and EU261 regulatory compensation rules, automated meal/hotel
voucher issuance, and digital boarding pass generation for re-accommodated passengers.
"""
import math
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.models.schemas import PassengerRecord, FlightSegment
from app.engine.baggage_engine import baggage_engine



# Geodesic coordinates for hub distance calculations
AIRPORT_COORDINATES = {
    "JFK": {"name": "New York John F. Kennedy", "lat": 40.6413, "lng": -73.7781, "city": "New York"},
    "ORD": {"name": "Chicago O'Hare", "lat": 41.9742, "lng": -87.9073, "city": "Chicago"},
    "LAX": {"name": "Los Angeles International", "lat": 33.9416, "lng": -118.4085, "city": "Los Angeles"},
    "DFW": {"name": "Dallas/Fort Worth", "lat": 32.8998, "lng": -97.0403, "city": "Dallas"},
    "ATL": {"name": "Hartsfield-Jackson Atlanta", "lat": 33.6407, "lng": -84.4277, "city": "Atlanta"},
    "SFO": {"name": "San Francisco International", "lat": 37.6213, "lng": -122.3790, "city": "San Francisco"},
    "MIA": {"name": "Miami International", "lat": 25.7959, "lng": -80.2870, "city": "Miami"},
    "DEN": {"name": "Denver International", "lat": 39.8561, "lng": -104.6737, "city": "Denver"},
    "BOS": {"name": "Boston Logan", "lat": 42.3656, "lng": -71.0096, "city": "Boston"},
    "SEA": {"name": "Seattle-Tacoma", "lat": 47.4502, "lng": -122.3088, "city": "Seattle"},
}


def haversine_distance_km(origin: str, destination: str) -> float:
    """Computes great-circle distance between two airports in kilometers."""
    c1 = AIRPORT_COORDINATES.get(origin, {"lat": 40.0, "lng": -74.0})
    c2 = AIRPORT_COORDINATES.get(destination, {"lat": 34.0, "lng": -118.0})

    lat1, lon1 = math.radians(c1["lat"]), math.radians(c1["lng"])
    lat2, lon2 = math.radians(c2["lat"]), math.radians(c2["lng"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return round(6371 * c, 1)


class CompensationEngine:
    def calculate_entitlements(self, pnr: PassengerRecord, delay_minutes: int = 180) -> Dict[str, Any]:
        """
        Calculates regulatory passenger compensation and e-vouchers
        based on EU261 and US DOT passenger protection standards.
        """
        distance_km = haversine_distance_km(pnr.origin, pnr.destination)

        # Compensation tiers based on distance & delay
        if distance_km < 1500:
            cash_compensation = 250
            tier = "Short-Haul (<1,500 km)"
        elif distance_km <= 3500:
            cash_compensation = 400
            tier = "Medium-Haul (1,500 - 3,500 km)"
        else:
            cash_compensation = 600
            tier = "Long-Haul (>3,500 km)"

        # Meal & Hotel voucher issuance
        meal_voucher = f"VCH-MEAL-{random.randint(1000, 9999)}"
        meal_amount = 30.00

        needs_hotel = delay_minutes >= 360 or (datetime.utcnow().hour >= 20 and delay_minutes >= 180)
        hotel_voucher = f"VCH-HTL-{random.randint(1000, 9999)}" if needs_hotel else None

        lounge_access = pnr.fare_class.value in ["J", "F"] or delay_minutes >= 240

        return {
            "pnr_id": pnr.pnr_id,
            "passenger_name": pnr.passenger_name,
            "route": f"{pnr.origin} -> {pnr.destination}",
            "distance_km": distance_km,
            "haul_tier": tier,
            "delay_minutes": delay_minutes,
            "cash_compensation_usd": cash_compensation if delay_minutes >= 180 else 0,
            "regulation": "EU261 / US-DOT Consumer Rule 14 CFR 259",
            "vouchers": {
                "meal_voucher_code": meal_voucher,
                "meal_amount_usd": meal_amount,
                "hotel_voucher_code": hotel_voucher,
                "hotel_provided": needs_hotel,
                "lounge_access_granted": lounge_access,
            },
        }

    def generate_boarding_pass(self, pnr: PassengerRecord, flight: Optional[FlightSegment] = None) -> Dict[str, Any]:
        """Generates an IATA-compliant digital boarding pass with seat, gate, and QR payload."""
        seat_num = f"{random.randint(1, 32)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
        gate = f"{random.choice(['B', 'C', 'D'])}{random.randint(2, 38)}"
        terminal = f"T{random.randint(1, 4)}"
        seq_num = f"{random.randint(10, 180):03d}"

        flight_num = flight.flight_number if flight else pnr.original_flight_number
        origin = flight.origin if flight else pnr.origin
        dest = flight.destination if flight else pnr.destination
        dep_time = flight.departure_time.isoformat() if flight else datetime.utcnow().isoformat()
        boarding_time = (
            (flight.departure_time - timedelta(minutes=40)).isoformat()
            if flight
            else (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        )

        qr_payload = f"M1{pnr.passenger_name.replace(' ', '/')[:20].ljust(20)}E{pnr.pnr_id} {origin}{dest}{flight_num} {seq_num}{pnr.fare_class.value}"

        return {
            "pnr_id": pnr.pnr_id,
            "passenger_name": pnr.passenger_name,
            "flight_number": flight_num,
            "carrier": flight_num[:2],
            "origin": origin,
            "destination": dest,
            "departure_time": dep_time,
            "boarding_time": boarding_time,
            "seat": seat_num,
            "gate": gate,
            "terminal": terminal,
            "boarding_group": "Group 2" if pnr.fare_class.value in ["J", "W"] else "Group 4",
            "sequence_number": seq_num,
            "fare_class": pnr.fare_class.value,
            "qr_data": qr_payload,
            "baggage_tags": [baggage_engine.get_baggage_record(pnr.pnr_id).get("iata_tag_number", f"001-{random.randint(100000, 999999)}")],
            "issued_at": datetime.utcnow().isoformat(),
        }



# Singleton instance
compensation_engine = CompensationEngine()

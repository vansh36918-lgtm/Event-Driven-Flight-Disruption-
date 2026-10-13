"""
Airborne In-Flight Diversion & Alternate Hub Intermodal Ground Engine.
Models FAA en-route weather diversions when destination hubs close due to CAT III minimums
or convective squall lines. Automatically schedules designated fuel alternates, calculates
ground charter motor coaches for short-haul distances (<150 mi), and re-routes passengers.
"""
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class AlternateAirport(BaseModel):
    iata_code: str
    name: str
    distance_miles_from_hub: int
    ground_coach_eligible: bool
    coach_transit_time_minutes: int
    has_customs_clearance: bool


class IntermodalCoachDispatch(BaseModel):
    dispatch_id: str
    carrier_contractor: str  # e.g., "AirOps Executive Coach Charter"
    departure_airport: str
    arrival_hub: str
    pickup_gate: str
    departure_time_utc: str
    estimated_arrival_utc: str
    transit_duration_minutes: int
    seats_allocated: int
    bus_plaque_code: str


class FlightDiversionRecord(BaseModel):
    diversion_id: str
    flight_number: str
    carrier: str
    origin: str
    scheduled_destination: str
    diverted_airport: str
    divert_reason: str
    divert_timestamp_utc: str
    resolution_type: str  # "INTERMODAL_COACH_DISPATCH" or "NEXT_DAY_FERRY_FLIGHT"
    coach_dispatch: Optional[IntermodalCoachDispatch]
    affected_passengers_count: int
    status: str  # "DIVERTED_GROUNDED", "COACH_BOARDING", "EN_ROUTE_SURFACE", "RESOLVED"


class DivertEngine:
    def __init__(self):
        self.alternates_map: Dict[str, List[AlternateAirport]] = {}
        self.active_diversions: Dict[str, FlightDiversionRecord] = {}  # diversion_id -> record
        self.flight_to_diversion: Dict[str, str] = {}  # flight_num -> diversion_id
        self._initialize_designated_alternates()

    def _initialize_designated_alternates(self):
        """Initializes FAA-approved designated fuel alternates for major hub airports."""
        self.alternates_map = {
            "ORD": [
                AlternateAirport(
                    iata_code="MKE",
                    name="Milwaukee Mitchell International Airport",
                    distance_miles_from_hub=80,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=85,
                    has_customs_clearance=True,
                ),
                AlternateAirport(
                    iata_code="IND",
                    name="Indianapolis International Airport",
                    distance_miles_from_hub=190,
                    ground_coach_eligible=False,
                    coach_transit_time_minutes=210,
                    has_customs_clearance=True,
                ),
            ],
            "JFK": [
                AlternateAirport(
                    iata_code="PHL",
                    name="Philadelphia International Airport",
                    distance_miles_from_hub=95,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=110,
                    has_customs_clearance=True,
                ),
                AlternateAirport(
                    iata_code="SWF",
                    name="New York Stewart International Airport",
                    distance_miles_from_hub=65,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=80,
                    has_customs_clearance=False,
                ),
            ],
            "ATL": [
                AlternateAirport(
                    iata_code="BHM",
                    name="Birmingham-Shuttlesworth International Airport",
                    distance_miles_from_hub=140,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=135,
                    has_customs_clearance=False,
                ),
                AlternateAirport(
                    iata_code="CHA",
                    name="Chattanooga Metropolitan Airport",
                    distance_miles_from_hub=115,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=120,
                    has_customs_clearance=False,
                ),
            ],
            "DFW": [
                AlternateAirport(
                    iata_code="AUS",
                    name="Austin-Bergstrom International Airport",
                    distance_miles_from_hub=195,
                    ground_coach_eligible=False,
                    coach_transit_time_minutes=215,
                    has_customs_clearance=True,
                ),
                AlternateAirport(
                    iata_code="OKC",
                    name="Will Rogers World Airport (Oklahoma City)",
                    distance_miles_from_hub=205,
                    ground_coach_eligible=False,
                    coach_transit_time_minutes=225,
                    has_customs_clearance=False,
                ),
            ],
            "LAX": [
                AlternateAirport(
                    iata_code="ONT",
                    name="Ontario International Airport",
                    distance_miles_from_hub=55,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=65,
                    has_customs_clearance=True,
                ),
                AlternateAirport(
                    iata_code="SAN",
                    name="San Diego International Airport",
                    distance_miles_from_hub=120,
                    ground_coach_eligible=True,
                    coach_transit_time_minutes=130,
                    has_customs_clearance=True,
                ),
            ],
        }

    def execute_flight_diversion(
        self,
        flight_number: str,
        origin: str,
        destination: str,
        carrier: str,
        affected_passengers: int = 145,
        reason: Optional[str] = None,
    ) -> FlightDiversionRecord:
        """
        Executes an emergency airborne diversion.
        Selects designated alternate, coordinates ramp ground handling,
        and dispatches chartered luxury intermodal coaches if <150 miles from destination.
        """
        # Return existing if already diverted
        if flight_number in self.flight_to_diversion:
            return self.active_diversions[self.flight_to_diversion[flight_number]]

        alternates = self.alternates_map.get(destination, [])
        if not alternates:
            # Fallback alternate
            alternate = AlternateAirport(
                iata_code="MKE",
                name="Milwaukee Mitchell International Airport",
                distance_miles_from_hub=80,
                ground_coach_eligible=True,
                coach_transit_time_minutes=85,
                has_customs_clearance=True,
            )
        else:
            alternate = alternates[0]

        now = datetime.utcnow()
        diversion_id = f"DIV-{flight_number}-{alternate.iata_code}"

        coach_dispatch = None
        if alternate.ground_coach_eligible:
            resolution = "INTERMODAL_COACH_DISPATCH"
            depart_coach = now + timedelta(minutes=45)  # 45 mins deplaning and baggage offload
            arrive_dest = depart_coach + timedelta(minutes=alternate.coach_transit_time_minutes)

            coach_dispatch = IntermodalCoachDispatch(
                dispatch_id=f"BUS-{flight_number}-{random.randint(1000, 9999)}",
                carrier_contractor="AirOps Executive Direct Motor Coach",
                departure_airport=alternate.iata_code,
                arrival_hub=destination,
                pickup_gate="Terminal South Charter Bus Concourse Door 3",
                departure_time_utc=depart_coach.isoformat() + "Z",
                estimated_arrival_utc=arrive_dest.isoformat() + "Z",
                transit_duration_minutes=alternate.coach_transit_time_minutes,
                seats_allocated=affected_passengers,
                bus_plaque_code=f"AIR-OPS-{random.randint(10, 99)}",
            )
        else:
            resolution = "NEXT_DAY_FERRY_FLIGHT"

        record = FlightDiversionRecord(
            diversion_id=diversion_id,
            flight_number=flight_number,
            carrier=carrier,
            origin=origin,
            scheduled_destination=destination,
            diverted_airport=alternate.iata_code,
            divert_reason=reason or "Destination Zero-Visibility CAT III Squall Line / Ground Stop",
            divert_timestamp_utc=now.isoformat() + "Z",
            resolution_type=resolution,
            coach_dispatch=coach_dispatch,
            affected_passengers_count=affected_passengers,
            status="DIVERTED_GROUNDED",
        )

        self.active_diversions[diversion_id] = record
        self.flight_to_diversion[flight_number] = diversion_id
        return record

    def get_diversion_by_flight(self, flight_number: str) -> Optional[FlightDiversionRecord]:
        div_id = self.flight_to_diversion.get(flight_number)
        if div_id and div_id in self.active_diversions:
            return self.active_diversions[div_id]
        return None

    def get_all_diversions(self) -> List[FlightDiversionRecord]:
        return list(self.active_diversions.values())

    def get_designated_alternates(self, hub: str) -> List[AlternateAirport]:
        return self.alternates_map.get(hub, [])


# Singleton instance
divert_engine = DivertEngine()

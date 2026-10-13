"""
Domain Models and Schemas for Flight Disruption & Autonomous Re-Accommodation Platform.
Strictly conforms to TravelTech (IATA, Sabre/Amadeus GDS, 6-char PNR) standards.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class FlightStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    BOARDING = "BOARDING"
    DEPARTED = "DEPARTED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    DIVERTED = "DIVERTED"


class DisruptionType(str, Enum):
    CANCELLATION = "CANCELLATION"
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    EQUIPMENT_CHANGE = "EQUIPMENT_CHANGE"
    WEATHER_DELAY = "WEATHER_DELAY"


class FareClass(str, Enum):
    ECONOMY = "Y"
    PREMIUM_ECONOMY = "W"
    BUSINESS = "J"
    FIRST = "F"


class FlightSegment(BaseModel):
    flight_number: str = Field(..., description="e.g. AA101, DL452, UA890")
    carrier: str = Field(..., description="2-letter IATA carrier code, e.g. AA, DL, UA")
    origin: str = Field(..., description="3-letter IATA airport code, e.g. JFK")
    destination: str = Field(..., description="3-letter IATA airport code, e.g. LAX")
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    seats_available: int = 50
    aircraft_type: str = "B737-800"
    status: FlightStatus = FlightStatus.SCHEDULED


class PassengerRecord(BaseModel):
    pnr_id: str = Field(..., description="6-character alphanumeric uppercase PNR (e.g. EK7P9X)")
    passenger_name: str
    email: str
    phone: str
    fare_class: FareClass = FareClass.ECONOMY
    original_flight_number: str
    origin: str
    destination: str
    status: str = "CONFIRMED"  # CONFIRMED, DISRUPTED, RE_ACCOMMODATED, REJECTED
    loyalty_tier: str = "GENERAL"  # DIAMOND, PLATINUM, GOLD, SILVER, GENERAL
    pvs_score: int = 450  # Passenger Value Score (100 - 1000)
    reaccommodation_options: List[Dict[str, Any]] = []
    selected_option_id: Optional[str] = None
    upgraded_cabin: Optional[str] = None
    upgrade_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DisruptionWebhookPayload(BaseModel):
    event_id: str
    disruption_type: DisruptionType
    flight_number: str
    carrier: str
    origin: str
    destination: str
    scheduled_departure: datetime
    estimated_departure: Optional[datetime] = None
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReaccommodationRoute(BaseModel):
    option_id: str
    route_type: str  # "DIRECT" or "CONNECTING"
    segments: List[FlightSegment]
    total_duration_minutes: int
    departure_time: datetime
    arrival_time: datetime
    departure_delay_minutes: int  # relative to original flight departure
    layover_airports: List[str] = []
    score: float = 0.0  # Graph heuristic score


class ChatMessageRequest(BaseModel):
    pnr_id: str
    message: str


class ChatMessageResponse(BaseModel):
    reply: str
    pnr_id: str
    detected_intent: str
    action_taken: Optional[str] = None
    suggested_options: Optional[List[Dict[str, Any]]] = None


class SystemMetrics(BaseModel):
    total_active_flights: int
    total_pnrs: int
    disrupted_flights: int
    affected_pnrs: int
    reaccommodated_pnrs: int
    autonomous_resolution_rate_pct: float
    avg_graph_solve_time_ms: float
    total_compensation_liability_usd: float = 0.0
    manual_hours_saved: float = 0.0


class AirportInfo(BaseModel):
    code: str
    name: str
    city: str
    lat: float
    lng: float


class TelemetryEventLog(BaseModel):
    event_id: str
    timestamp: str
    flight_number: str
    disruption_type: str
    origin: str
    destination: str
    affected_count: int
    latency_ms: float
    status: str


class VoiceCommandRequest(BaseModel):
    command: str = Field(..., description="Spoken or typed voice command for JARVIS")
    pnr_id: Optional[str] = None
    current_tab: Optional[str] = "ops"


class VoiceCommandResponse(BaseModel):
    command: str
    intent: str
    action: str
    target: Optional[str] = None
    speech_response: str
    ui_action: Optional[Dict[str, Any]] = None
    status: str = "SUCCESS"


class BookingCheckoutRequest(BaseModel):
    flight_number: str
    origin: str
    destination: str
    passenger_name: str
    email: str
    phone: Optional[str] = "+91 98765 43210"
    cabin_class: str = "ECONOMY"  # ECONOMY, BUSINESS, CHARTER
    payment_method: str = "UPI"  # UPI, CREDIT_CARD, NET_BANKING, SABRE_CORP
    amount_inr: float = 6450.0
    amount_paid: Optional[float] = None


class BookingCheckoutResponse(BaseModel):
    pnr_id: str
    transaction_id: str
    flight_number: str
    origin: str
    destination: str
    passenger_name: str
    cabin_class: str
    seat: str
    gate: str
    seat_assigned: Optional[str] = None
    gate_assigned: Optional[str] = None
    baggage_rfid_tag: Optional[str] = None
    status: str = "CONFIRMED"
    payment_status: str = "PAID"
    amount_inr: float
    amount_paid: Optional[float] = None
    payment_method: str
    timestamp: str
    message: str




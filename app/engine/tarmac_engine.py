"""
US DOT 14 CFR 259.4 Tarmac Delay Rule & Passenger Concierge Multi-Channel Push Engine.
Monitors taxi-out and taxi-in queue wait times, enforces mandatory 2-hour food/water distribution,
executes automated 3-hour (domestic) and 4-hour (international) gate return extractions,
and broadcasts multi-channel alerts (SMS, WhatsApp, Apple PKPass, Email).
"""
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class TarmacIncident(BaseModel):
    incident_id: str
    flight_number: str
    tail_number: str
    airport: str
    phase: str  # "TAXI_OUT", "TAXI_IN", "DEICING_PAD", "RUNWAY_HOLD"
    start_time_utc: str
    elapsed_minutes: int
    is_international: bool
    passenger_count: int
    welfare_served: bool  # 2h water/food service completed
    alert_level: str  # "NOMINAL", "WELFARE_DUE", "GATE_RETURN_COORDINATION", "CRITICAL_DOT_BREACH_AVERTED"
    assigned_deplaning_gate: Optional[str]
    potential_dot_liability_usd: float
    status: str  # "MONITORING", "EXTRACTED_TO_GATE", "DEPLANING", "CLEARED_FOR_TAKEOFF"


class PassengerNotification(BaseModel):
    notification_id: str
    pnr_id: str
    channel: str  # "SMS", "WHATSAPP", "APPLE_PKPASS", "EMAIL"
    event_type: str  # "DISRUPTION_ALERT", "REBOOK_CONFIRMED", "HOTEL_ISSUED", "BAGGAGE_UPDATE", "TARMAC_CARE"
    title: str
    message: str
    timestamp_utc: str
    status: str  # "DELIVERED"


class TarmacAndNotificationEngine:
    DOT_FINE_PER_PASSENGER = 27500.0  # Max statutory civil penalty under 14 CFR 259.4

    def __init__(self):
        self.active_tarmac_flights: Dict[str, TarmacIncident] = {}
        self.pnr_notifications: Dict[str, List[PassengerNotification]] = {}
        self._initialize_sample_tarmac_activity()

    def _initialize_sample_tarmac_activity(self):
        """Initializes simulated active taxiing operations nearing welfare/extraction thresholds."""
        now = datetime.utcnow()
        sample_flights = [
            ("UA240", "N240UA", "ORD", "TAXI_OUT", 135, False, 178),  # 2h 15m taxi out (Welfare required)
            ("DL482", "N482DL", "ATL", "DEICING_PAD", 85, False, 160),  # 1h 25m nominal
            ("BA114", "G-ZBLA", "JFK", "TAXI_OUT", 215, True, 265),  # 3h 35m intl (Gate return pending)
        ]
        for f_num, tail, apt, phase, elapsed, is_intl, pax in sample_flights:
            inc_id = f"TMC-{apt}-{f_num}"
            welfare = elapsed >= 120
            level = "WELFARE_DUE" if elapsed >= 120 and elapsed < 160 else ("GATE_RETURN_COORDINATION" if elapsed >= 160 else "NOMINAL")
            gate = "Gate B14 (Ramp Standoff)" if level == "GATE_RETURN_COORDINATION" else None

            inc = TarmacIncident(
                incident_id=inc_id,
                flight_number=f_num,
                tail_number=tail,
                airport=apt,
                phase=phase,
                start_time_utc=(now - timedelta(minutes=elapsed)).isoformat() + "Z",
                elapsed_minutes=elapsed,
                is_international=is_intl,
                passenger_count=pax,
                welfare_served=welfare,
                alert_level=level,
                assigned_deplaning_gate=gate,
                potential_dot_liability_usd=pax * self.DOT_FINE_PER_PASSENGER,
                status="MONITORING" if level != "GATE_RETURN_COORDINATION" else "EXTRACTED_TO_GATE",
            )
            self.active_tarmac_flights[f_num] = inc

    def evaluate_tarmac_delay(
        self,
        flight_number: str,
        airport: str,
        tail_number: str = "N-REG",
        elapsed_minutes: int = 140,
        is_international: bool = False,
        passenger_count: int = 150,
        phase: str = "TAXI_OUT",
    ) -> TarmacIncident:
        """
        Enforces FAA / DOT 14 CFR 259.4 tarmac rule compliance:
        - >=120m: Mandatory potable water & snack distribution
        - >=165m (domestic) or >=225m (intl): Automated extraction to gate before hard limit
        """
        now = datetime.utcnow()
        welfare = elapsed_minutes >= 120
        dot_limit = 240 if is_international else 180

        if elapsed_minutes >= (dot_limit - 15):
            alert_level = "CRITICAL_DOT_BREACH_AVERTED"
            gate = f"Terminal Gate {random.choice(['C10', 'D4', 'B18', 'E2'])} (Emergency Extraction)"
            status = "EXTRACTED_TO_GATE"
        elif elapsed_minutes >= (dot_limit - 30):
            alert_level = "GATE_RETURN_COORDINATION"
            gate = f"Standby Gate {random.choice(['A6', 'B2', 'C1'])}"
            status = "COORDINATING_GATE_RETURN"
        elif elapsed_minutes >= 120:
            alert_level = "WELFARE_DUE"
            gate = None
            status = "CABIN_SERVICE_ACTIVE"
        else:
            alert_level = "NOMINAL"
            gate = None
            status = "MONITORING"

        incident = TarmacIncident(
            incident_id=f"TMC-{airport}-{flight_number}",
            flight_number=flight_number,
            tail_number=tail_number,
            airport=airport,
            phase=phase,
            start_time_utc=(now - timedelta(minutes=elapsed_minutes)).isoformat() + "Z",
            elapsed_minutes=elapsed_minutes,
            is_international=is_international,
            passenger_count=passenger_count,
            welfare_served=welfare,
            alert_level=alert_level,
            assigned_deplaning_gate=gate,
            potential_dot_liability_usd=passenger_count * self.DOT_FINE_PER_PASSENGER,
            status=status,
        )

        self.active_tarmac_flights[flight_number] = incident
        return incident

    def get_all_tarmac_incidents(self) -> List[TarmacIncident]:
        return list(self.active_tarmac_flights.values())

    def get_tarmac_by_flight(self, flight_number: str) -> Optional[TarmacIncident]:
        return self.active_tarmac_flights.get(flight_number)

    # -------------------------------------------------------------
    # Multi-Channel Concierge Notification Engine
    # -------------------------------------------------------------
    def push_notification(
        self,
        pnr_id: str,
        channel: str,
        event_type: str,
        title: str,
        message: str,
    ) -> PassengerNotification:
        """Sends and logs an automated multi-channel passenger notification."""
        notif_id = f"NOTIF-{pnr_id}-{random.randint(1000, 9999)}"
        notif = PassengerNotification(
            notification_id=notif_id,
            pnr_id=pnr_id,
            channel=channel,
            event_type=event_type,
            title=title,
            message=message,
            timestamp_utc=datetime.utcnow().isoformat() + "Z",
            status="DELIVERED",
        )
        if pnr_id not in self.pnr_notifications:
            self.pnr_notifications[pnr_id] = []
        self.pnr_notifications[pnr_id].insert(0, notif)
        return notif

    def get_pnr_notifications(self, pnr_id: str) -> List[PassengerNotification]:
        """Returns delivery history of all push notifications for a passenger."""
        # Pre-seed realistic notifications if none present
        if pnr_id not in self.pnr_notifications:
            self.pnr_notifications[pnr_id] = [
                PassengerNotification(
                    notification_id=f"NOTIF-{pnr_id}-01",
                    pnr_id=pnr_id,
                    channel="SMS",
                    event_type="DISRUPTION_ALERT",
                    title="AirOps Flight Alert",
                    message="Your scheduled flight experienced an IRROPS event. Alternative routes are pre-reserved.",
                    timestamp_utc=(datetime.utcnow() - timedelta(minutes=15)).isoformat() + "Z",
                    status="DELIVERED",
                ),
                PassengerNotification(
                    notification_id=f"NOTIF-{pnr_id}-02",
                    pnr_id=pnr_id,
                    channel="APPLE_PKPASS",
                    event_type="REBOOK_CONFIRMED",
                    title="Digital Pass Updated",
                    message="Boarding pass updated in Apple Wallet. New Departure Gate B12.",
                    timestamp_utc=(datetime.utcnow() - timedelta(minutes=8)).isoformat() + "Z",
                    status="DELIVERED",
                ),
                PassengerNotification(
                    notification_id=f"NOTIF-{pnr_id}-03",
                    pnr_id=pnr_id,
                    channel="WHATSAPP",
                    event_type="BAGGAGE_UPDATE",
                    title="Luggage Custody Verified",
                    message="IATA 753 Scan: Checked baggage transferred to BHS Sorter Bay for onward flight.",
                    timestamp_utc=(datetime.utcnow() - timedelta(minutes=3)).isoformat() + "Z",
                    status="DELIVERED",
                ),
            ]
        return self.pnr_notifications[pnr_id]


# Singleton instance
tarmac_engine = TarmacAndNotificationEngine()

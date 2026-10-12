"""
Autonomous Re-Accommodation Worker.
Processes disruption events (cancellations/delays), queries affected PNRs,
and invokes the NetworkX constrained graph search algorithm to discover valid alternatives.
"""
import time
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.engine.gds_service import gds_service
from app.engine.graph_engine import reaccommodation_engine
from app.engine.crew_engine import crew_engine
from app.engine.fleet_engine import fleet_engine
from app.models.schemas import FlightStatus

logger = logging.getLogger("Worker")


class ReaccommodationWorker:
    def __init__(self):
        self.total_processed_events = 0
        self.total_reaccommodated_pnrs = 0
        self.last_solve_time_ms = 0.0
        self.telemetry_logs: List[Dict[str, Any]] = []
        self.crew_alerts: List[Dict[str, Any]] = []
        self.tail_swaps: List[Dict[str, Any]] = []

    async def handle_disruption_event(self, event_data: Dict[str, Any]):
        """Callback invoked when a flight disruption event is published on the bus."""
        start_time = time.perf_counter()
        flight_num = event_data.get("flight_number")
        disruption_type = event_data.get("disruption_type")
        logger.info(f"Worker received event: {flight_num} -> {disruption_type}")

        flight = gds_service.get_flight(flight_num)
        if not flight:
            logger.warning(f"Flight {flight_num} not found in GDS inventory.")
            return

        # Mark flight in GDS
        new_status = FlightStatus.CANCELLED if disruption_type == "CANCELLATION" else FlightStatus.DELAYED
        gds_service.update_flight_status(flight_num, new_status)

        # Refresh NetworkX active graph with current operational flights
        all_flights = list(gds_service.flights.values())
        reaccommodation_engine.build_schedule_graph(all_flights)

        # Query all PNRs booked on this disrupted flight and prioritize by Passenger Value Score (PVS)
        affected_pnrs = gds_service.get_pnrs_for_flight(flight_num)
        affected_pnrs.sort(key=lambda p: getattr(p, "pvs_score", 400), reverse=True)
        logger.info(f"Identified {len(affected_pnrs)} affected PNRs on flight {flight_num}. Ranked by PVS priority.")

        # For each affected passenger, compute alternative routes within 4-hour window
        scheduled_dep = flight.departure_time
        origin = flight.origin
        dest = flight.destination

        # 1. Compute Pareto-optimal alternative routes with carrier affinity and PVS weighting
        routes = reaccommodation_engine.find_alternatives(
            origin=origin,
            destination=dest,
            original_departure=scheduled_dep,
            max_window_hours=4,
            preferred_carrier=flight.carrier,
            pvs_score=affected_pnrs[0].pvs_score if affected_pnrs else 400,
        )

        routes_payload = [r.model_dump(mode="json") for r in routes]

        for pnr in affected_pnrs:
            gds_service.update_pnr_reaccommodation(pnr.pnr_id, routes_payload)
            self.total_reaccommodated_pnrs += 1

        # 2. Check for cascading crew timeout violations under FAA Part 117
        delay_est = 180 if disruption_type == "CANCELLATION" else 120
        cascading = crew_engine.evaluate_cascading_timeout(flight_num, delay_minutes=delay_est)
        for alert in cascading:
            logger.warning(
                f"ALERT: Cascading FAA Part 117 duty timeout on downstream flight {alert['cascading_flight_number']} "
                f"from antecedent {flight_num}."
            )
            self.crew_alerts.insert(0, alert)
            if len(self.crew_alerts) > 20:
                self.crew_alerts.pop()

        # 3. Evaluate operational fleet tail-swap to salvage aircraft rotation
        swap = fleet_engine.evaluate_tail_swap(flight_num, origin, flight.carrier)
        if swap:
            logger.info(
                f"Fleet OCC executed tail swap: {swap['original_tail']} -> {swap['assigned_spare_tail']} "
                f"at {origin} for flight {flight_num}."
            )
            self.tail_swaps.insert(0, swap)
            if len(self.tail_swaps) > 20:
                self.tail_swaps.pop()

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.last_solve_time_ms = round(elapsed_ms, 2)
        self.total_processed_events += 1

        # Keep last 50 telemetry events for real-time streaming
        log_entry = {
            "event_id": event_data.get("event_id", f"EVT-{int(time.time()*1000)}"),
            "timestamp": datetime.utcnow().strftime("%H:%M:%S UTC"),
            "flight_number": flight_num,
            "disruption_type": disruption_type,
            "origin": origin,
            "destination": dest,
            "affected_count": len(affected_pnrs),
            "latency_ms": self.last_solve_time_ms,
            "status": "AUTO_RESOLVED",
        }
        self.telemetry_logs.insert(0, log_entry)
        if len(self.telemetry_logs) > 50:
            self.telemetry_logs.pop()

        logger.info(
            f"Autonomous Re-Accommodation completed for {len(affected_pnrs)} PNRs in {self.last_solve_time_ms}ms. "
            f"Found {len(routes)} viable alternative routes."
        )


# Singleton worker
reaccommodation_worker = ReaccommodationWorker()

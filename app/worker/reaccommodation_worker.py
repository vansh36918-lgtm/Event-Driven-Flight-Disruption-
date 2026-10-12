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
from app.models.schemas import FlightStatus

logger = logging.getLogger("Worker")


class ReaccommodationWorker:
    def __init__(self):
        self.total_processed_events = 0
        self.total_reaccommodated_pnrs = 0
        self.last_solve_time_ms = 0.0

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

        # Query all PNRs booked on this disrupted flight
        affected_pnrs = gds_service.get_pnrs_for_flight(flight_num)
        logger.info(f"Identified {len(affected_pnrs)} affected PNRs on flight {flight_num}.")

        # For each affected passenger, compute alternative routes within 4-hour window
        scheduled_dep = flight.departure_time
        origin = flight.origin
        dest = flight.destination

        routes = reaccommodation_engine.find_alternatives(
            origin=origin,
            destination=dest,
            original_departure=scheduled_dep,
            max_window_hours=4,
        )

        routes_payload = [r.model_dump(mode="json") for r in routes]

        for pnr in affected_pnrs:
            gds_service.update_pnr_reaccommodation(pnr.pnr_id, routes_payload)
            self.total_reaccommodated_pnrs += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.last_solve_time_ms = round(elapsed_ms, 2)
        self.total_processed_events += 1
        logger.info(
            f"Autonomous Re-Accommodation completed for {len(affected_pnrs)} PNRs in {self.last_solve_time_ms}ms. "
            f"Found {len(routes)} viable alternative routes."
        )


# Singleton worker
reaccommodation_worker = ReaccommodationWorker()

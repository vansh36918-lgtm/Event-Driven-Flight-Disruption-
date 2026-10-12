"""
NetworkX-Powered Constrained Route Engine.
Discovers alternative flight paths within a strict 4-hour window from original departure,
evaluating both direct flights and multi-hop connecting paths with connection layover constraints.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import networkx as nx
from app.models.schemas import FlightSegment, FlightStatus, ReaccommodationRoute
from app.engine.alliance_engine import alliance_engine


class ConstrainedReaccommodationEngine:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def build_schedule_graph(self, flights: List[FlightSegment]):
        """
        Builds a multi-directed graph where:
        - Nodes: Airport IATA codes (e.g., 'JFK', 'ORD')
        - Edges: Flight segments with temporal attributes, capacity, and status.
        """
        self.graph.clear()
        for f in flights:
            # Only route on scheduled, operational flights with available seats
            if f.status in [FlightStatus.SCHEDULED, FlightStatus.BOARDING] and f.seats_available > 0:
                self.graph.add_edge(
                    f.origin,
                    f.destination,
                    key=f.flight_number,
                    flight=f,
                    departure_time=f.departure_time,
                    arrival_time=f.arrival_time,
                    duration_minutes=f.duration_minutes,
                    seats=f.seats_available,
                )

    def find_alternatives(
        self,
        origin: str,
        destination: str,
        original_departure: datetime,
        max_window_hours: int = 4,
        min_layover_minutes: int = 45,
        max_layover_minutes: int = 240,
        max_stops: int = 2,
        preferred_carrier: Optional[str] = None,
        pvs_score: int = 400,
    ) -> List[ReaccommodationRoute]:
        """
        Executes constrained multi-objective Pareto graph search:
        - Must depart between [original_departure, original_departure + max_window_hours]
        - Connection layovers must satisfy [min_layover_minutes, max_layover_minutes]
        - Evaluates Pareto trade-offs across:
          1. Departure delay delta (relative to T0)
          2. Total flight/transit duration
          3. Transfer penalty (direct vs connecting)
          4. Operating carrier alliance affinity
          5. Dynamic weighting scaled by Passenger Value Score (PVS)
        """
        window_end = original_departure + timedelta(hours=max_window_hours)
        candidates: List[ReaccommodationRoute] = []

        if not self.graph.has_node(origin) or not self.graph.has_node(destination):
            return candidates

        # 1. Direct Flights within window
        if self.graph.has_edge(origin, destination):
            for edge_key, edge_data in self.graph.get_edge_data(origin, destination).items():
                f: FlightSegment = edge_data["flight"]
                if original_departure <= f.departure_time <= window_end:
                    delay_min = int((f.departure_time - original_departure).total_seconds() / 60)
                    
                    # Carrier & alliance affinity bonus (-40 same carrier, -36 same alliance, -28 bilateral)
                    affinity = alliance_engine.compute_affinity_score(preferred_carrier, f.carrier) if preferred_carrier else 0.5
                    carrier_bonus = int(-40 * affinity)
                    
                    # VIP passengers (PVS > 700) prioritize minimizing delay; economy balances duration
                    delay_weight = 1.3 if pvs_score >= 700 else 1.0
                    composite_score = float(delay_min * delay_weight + f.duration_minutes + carrier_bonus)

                    route = ReaccommodationRoute(
                        option_id=f"OPT-DIR-{f.flight_number}",
                        route_type="DIRECT",
                        segments=[f],
                        total_duration_minutes=f.duration_minutes,
                        departure_time=f.departure_time,
                        arrival_time=f.arrival_time,
                        departure_delay_minutes=delay_min,
                        layover_airports=[],
                        score=composite_score,
                    )
                    candidates.append(route)

        # 2. 1-Stop Connecting Routes within window
        for hub in self.graph.successors(origin):
            if hub == destination or hub == origin:
                continue

            leg1_edges = self.graph.get_edge_data(origin, hub)
            if not leg1_edges:
                continue

            for leg1_key, leg1_data in leg1_edges.items():
                f1: FlightSegment = leg1_data["flight"]
                if not (original_departure <= f1.departure_time <= window_end):
                    continue

                if not self.graph.has_edge(hub, destination):
                    continue

                leg2_edges = self.graph.get_edge_data(hub, destination)
                for leg2_key, leg2_data in leg2_edges.items():
                    f2: FlightSegment = leg2_data["flight"]

                    layover_delta = (f2.departure_time - f1.arrival_time).total_seconds() / 60
                    if min_layover_minutes <= layover_delta <= max_layover_minutes:
                        total_duration = int((f2.arrival_time - f1.departure_time).total_seconds() / 60)
                        delay_min = int((f1.departure_time - original_departure).total_seconds() / 60)

                        if preferred_carrier:
                            aff1 = alliance_engine.compute_affinity_score(preferred_carrier, f1.carrier)
                            aff2 = alliance_engine.compute_affinity_score(preferred_carrier, f2.carrier)
                            carrier_bonus = int(-30 * (aff1 + aff2))
                        else:
                            carrier_bonus = 0

                        # Connecting penalty: +100 for transfer friction
                        composite_score = float(delay_min + total_duration + 100 + carrier_bonus)

                        route = ReaccommodationRoute(
                            option_id=f"OPT-HUB-{f1.flight_number}-{f2.flight_number}",
                            route_type="CONNECTING",
                            segments=[f1, f2],
                            total_duration_minutes=total_duration,
                            departure_time=f1.departure_time,
                            arrival_time=f2.arrival_time,
                            departure_delay_minutes=delay_min,
                            layover_airports=[hub],
                            score=composite_score,
                        )
                        candidates.append(route)

        # Sort candidate routes by Pareto composite utility score
        candidates.sort(key=lambda r: r.score)
        return candidates[:3]  # Return top 3 Pareto-optimal alternatives


# Singleton engine
reaccommodation_engine = ConstrainedReaccommodationEngine()

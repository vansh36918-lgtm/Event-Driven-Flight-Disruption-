"""
CLI Disruption & Telemetry Simulation Runner.
Simulates real-time GDS flight telemetry webhooks, automatically detecting
cancellations and schedule changes across booked PNRs.
Usage:
    python simulate_disruption.py [FLIGHT_NUMBER]
Example:
    python simulate_disruption.py AA100
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from app.engine.gds_service import gds_service

API_BASE_URL = "http://localhost:8000"


def run_simulation(flight_num: str = None):
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
            # Query live server flights
            if not flight_num:
                flights_resp = client.get("/api/v1/flights?limit=20")
                if flights_resp.status_code != 200 or not flights_resp.json():
                    print("[ERROR] Could not fetch flights from server.")
                    return
                live_flights = flights_resp.json()
                # Pick first flight with booked passengers
                target = next((f for f in live_flights if f.get("booked_passengers", 0) > 0), live_flights[0])
                flight_num = target["flight_number"]
                origin = target["origin"]
                dest = target["destination"]
                carrier = target["carrier"]
                dep_time = target["departure_time"]
                sample_pnr = target.get("sample_pnr")
            else:
                flight = gds_service.get_flight(flight_num)
                origin = flight.origin if flight else "JFK"
                dest = flight.destination if flight else "ORD"
                carrier = flight.carrier if flight else "AA"
                dep_time = flight.departure_time.isoformat() if flight else "2026-10-13T12:00:00"
                sample_pnr = gds_service.flight_to_pnrs.get(flight_num, [None])[0]

            print("=" * 70)
            print(f"DISRUPTION SIMULATION: Grounding Flight {flight_num} ({origin} -> {dest})")
            print("=" * 70)
            payload = {
                "event_id": f"SIM-EVT-{int(time.time())}",
                "disruption_type": "CANCELLATION",
                "flight_number": flight_num,
                "carrier": carrier,
                "origin": origin,
                "destination": dest,
                "scheduled_departure": dep_time if isinstance(dep_time, str) else dep_time.isoformat(),
                "reason": "Simulated Severe Weather Ground Stop",
            }

            print("[1] Emitting Disruption Webhook to Platform...")
            resp = client.post("/api/v1/gds/simulate-disruption", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                print(f"    Status: {data.get('status')}")
                print(f"    Affected PNRs: {data.get('affected_pnrs')}")
                print(f"    Graph Solve Latency: {data.get('solve_time_ms')} ms")

                # Sample affected passenger
                if not sample_pnr:
                    sample_pnr = gds_service.flight_to_pnrs.get(flight_num, [None])[0]
                if sample_pnr:
                    print("\n[2] Inspecting Passenger PNR Re-Accommodation State:")
                    pnr_resp = client.get(f"/api/v1/pnr/{sample_pnr}")
                    pnr_data = pnr_resp.json()
                    print(f"    Passenger: {pnr_data.get('passenger_name')} (PNR: {sample_pnr})")
                    print(f"    State: {pnr_data.get('status')}")
                    print(f"    Generated Alternatives ({len(pnr_data.get('reaccommodation_options'))} options):")
                    for idx, opt in enumerate(pnr_data.get("reaccommodation_options")):
                        print(f"      Option {idx + 1}: {opt.get('route_type')} | +{opt.get('departure_delay_minutes')}m departure | Duration: {opt.get('total_duration_minutes')}m")

                    print("\n[3] Testing Autonomous AI Concierge Re-Ticketing:")
                    chat_resp = client.post(
                        "/api/v1/chat",
                        json={"pnr_id": sample_pnr, "message": "Please confirm and book Option 1"},
                    )
                    print("    AI Agent Reply:")
                    for line in chat_resp.json().get("reply", "").splitlines():
                        print(f"      {line}")
            else:
                print(f"[ERROR] API returned {resp.status_code}: {resp.text}")
    except httpx.ConnectError:
        print("[WARNING] Local API server is not running on http://localhost:8000.")
        print("Run 'python run.py' first in a terminal, or run 'python test_system.py' for offline testing.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_simulation(target)

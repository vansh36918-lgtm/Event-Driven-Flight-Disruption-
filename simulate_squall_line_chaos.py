"""
Multi-Hub Squall Line Storm Chaos Simulator.
Simulates a multi-hub severe weather event (derecho/squall line across ORD, DFW, ATL, JFK)
emitting 20+ concurrent disruption events to stress-test asynchronous throughput,
PVS priority solving, FAA Part 117 crew timeouts, fleet tail-swaps, and CDM slot swaps.
"""
import sys
import time
import asyncio
import httpx
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"


async def trigger_flight_disruption(client: httpx.AsyncClient, flight: Dict[str, Any], event_code: str) -> Dict[str, Any]:
    f_num = flight.get("flight_number")
    payload = {
        "event_id": f"SQUALL-EVT-{f_num}-{int(time.time()*1000)%100000}",
        "disruption_type": "CANCELLATION" if event_code == "CANCELLATION" else "WEATHER_DELAY",
        "flight_number": f_num,
        "carrier": flight.get("carrier", f_num[:2]),
        "origin": flight.get("origin"),
        "destination": flight.get("destination"),
        "scheduled_departure": flight.get("departure_time"),
        "reason": "SEVERE CONVECTIVE SQUALL LINE / GROUND STOP ORDER",
    }
    try:
        t0 = time.perf_counter()
        res = await client.post(f"{BASE_URL}/api/v1/gds/simulate-disruption", json=payload, timeout=10.0)
        elapsed = (time.perf_counter() - t0) * 1000
        if res.status_code == 200:
            data = res.json()
            data["http_latency_ms"] = round(elapsed, 2)
            return data
        else:
            return {"flight_number": f_num, "status": "FAILED", "code": res.status_code}
    except Exception as e:
        return {"flight_number": f_num, "status": "ERROR", "error": str(e)}


async def run_squall_line_chaos():
    print("=" * 70)
    print("SQUALL LINE MULTI-HUB CONVECTIVE STORM CHAOS SIMULATION")
    print("TARGET HUBS: ORD (Chicago) | DFW (Dallas) | ATL (Atlanta) | JFK (New York)")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # 1. Fetch active flights from server
        flights_res = await client.get(f"{BASE_URL}/api/v1/flights?limit=200")
        if flights_res.status_code != 200:
            print("ERR: Server not reachable at http://localhost:8000.")
            return

        all_flights = flights_res.json()
        target_hubs = {"ORD", "DFW", "ATL", "JFK"}
        squall_targets = [
            f for f in all_flights
            if f.get("origin") in target_hubs or f.get("destination") in target_hubs
        ][:20]

        print(f"Selected {len(squall_targets)} high-density hub flights for simultaneous storm grounding.\n")

        # 2. Concurrently inject disruptions
        start_time = time.perf_counter()
        tasks = [
            trigger_flight_disruption(client, f, "CANCELLATION" if i % 2 == 0 else "WEATHER_DELAY")
            for i, f in enumerate(squall_targets)
        ]
        results = await asyncio.gather(*tasks)
        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 3. Print individual execution metrics
        print(f"{'FLIGHT':<10} | {'ORIGIN':<6} | {'DEST':<6} | {'AFFECTED':<10} | {'SOLVE LATENCY':<15} | {'STATUS'}")
        print("-" * 70)
        total_pax_affected = 0
        for i, res in enumerate(results):
            f_obj = squall_targets[i]
            if res.get("status") == "PROCESSED":
                pax = res.get("affected_pnrs", 0)
                total_pax_affected += pax
                solve_ms = res.get("solve_time_ms", 0.0)
                print(f"{f_obj['flight_number']:<10} | {f_obj['origin']:<6} | {f_obj['destination']:<6} | {pax:<10} | {solve_ms} ms{'':<8} | RESOLVED")
            else:
                print(f"{f_obj['flight_number']:<10} | {f_obj['origin']:<6} | {f_obj['destination']:<6} | N/A        | ERROR           | FAILED")

        print("-" * 70)
        print(f"Total Flights Grounded    : {len(squall_targets)}")
        print(f"Total Disrupted PNRs      : {total_pax_affected}")
        print(f"Total Pipeline Burst Time : {total_time_ms} ms")
        print(f"Avg Re-Accommodation Lat  : {round(total_time_ms / max(len(squall_targets), 1), 2)} ms/flight")

        # 4. Fetch system-wide metrics and ATC CDM slot status
        metrics_res = await client.get(f"{BASE_URL}/api/v1/metrics")
        slots_res = await client.get(f"{BASE_URL}/api/v1/atc/slot-swaps")
        tail_res = await client.get(f"{BASE_URL}/api/v1/fleet/tail-swaps")
        crew_res = await client.get(f"{BASE_URL}/api/v1/crew/alerts")

        if metrics_res.status_code == 200:
            m = metrics_res.json()
            print("\n" + "=" * 70)
            print("POST-CHAOS PLATFORM STATUS:")
            print(f" - Total Re-accommodated PNRs : {m.get('reaccommodated_pnrs')}")
            print(f" - Autonomous Resolution Rate : {m.get('autonomous_resolution_rate_pct')}%")
            print(f" - Agent Labor Saved          : {m.get('manual_hours_saved')} hours")
            print(f" - Est EU261/DOT Liability    : ${m.get('total_compensation_liability_usd', 0):,.2f}")
            print(f" - Active Tail-Swaps Executed : {len(tail_res.json()) if tail_res.status_code == 200 else 0}")
            print(f" - CDM Slot Swaps Confirmed   : {len(slots_res.json()) if slots_res.status_code == 200 else 0}")
            print(f" - Part 117 Crew Breaches     : {len(crew_res.json()) if crew_res.status_code == 200 else 0}")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_squall_line_chaos())

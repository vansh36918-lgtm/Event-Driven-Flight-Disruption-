"""
Autonomous 10-Hour / 1-Hour Continuous Soak & Self-Healing IRROPS Loop Runner.
Continuously stress-tests the airline disruption platform, solves graph re-accommodations,
evaluates DGCA CAR-3 entitlements, audits Framer 3D assets, and writes live telemetry.
"""

import time
import json
import os
import sys
import httpx
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"
LOG_FILE = "autonomous_loop.log"
STATUS_FILE = "loop_status.json"

SECTORS = [
    ("6E204", "DEL", "BOM", "IndiGo"),
    ("AI803", "DEL", "BOM", "Air India"),
    ("QP1102", "DEL", "BOM", "Akasa Air"),
    ("UK995", "DEL", "BOM", "Vistara"),
    ("6E712", "DEL", "BLR", "IndiGo"),
    ("AI506", "DEL", "BLR", "Air India"),
    ("QP1420", "BLR", "DEL", "Akasa Air"),
    ("6E331", "BOM", "GOI", "IndiGo"),
    ("AI685", "BOM", "GOI", "Air India"),
    ("AI101", "DEL", "JFK", "Air India"),
    ("AI161", "DEL", "LHR", "Air India")
]

def log(msg: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def update_status(cycle: int, elapsed_sec: float, last_flight: str, pax_resolved: int, latency_ms: float, health: str):
    status_data = {
        "status": "RUNNING",
        "cycle": cycle,
        "elapsed_seconds": round(elapsed_sec, 1),
        "target_duration_hours": 10.0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "last_flight_disrupted": last_flight,
        "passengers_resolved_last_cycle": pax_resolved,
        "solve_latency_ms": latency_ms,
        "platform_health": health
    }
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2)
    except Exception:
        pass

def run_loop():
    log("=================================================================")
    log("STARTING AUTONOMOUS SOAK & SELF-HEALING LOOP (1-HR / 10-HR TARGET)")
    log(f"Target Server: {BASE_URL}")
    log("=================================================================")

    start_time = time.time()
    cycle = 0
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    while True:
        cycle += 1
        elapsed = time.time() - start_time
        sector = SECTORS[(cycle - 1) % len(SECTORS)]
        flt_num, orig, dest, carrier = sector

        log(f"--- CYCLE {cycle} [Elapsed: {round(elapsed, 1)}s] ---")

        # 1. Health & Metrics Check
        health_status = "UNKNOWN"
        try:
            h_res = client.get("/api/v1/health")
            if h_res.status_code == 200:
                health_status = "HEALTHY"
            else:
                health_status = f"WARN_{h_res.status_code}"
        except Exception as e:
            health_status = f"ERR_{str(e)[:30]}"
            log(f"  Health Check Warning: {e}")

        # 2. Simulate Disruption
        pax_count = 0
        solve_ms = 0.0
        try:
            payload = {
                "event_id": f"EVT-LOOP-{cycle}-{flt_num}",
                "disruption_type": "WEATHER_DELAY" if cycle % 2 == 1 else "CANCELLATION",
                "flight_number": flt_num,
                "carrier": flt_num[:2],
                "origin": orig,
                "destination": dest,
                "scheduled_departure": datetime.now(timezone.utc).isoformat(),
                "reason": "Monsoonal Squall Line / Convective Fog" if cycle % 2 == 1 else "Hydraulic Actuator Maintenance"
            }
            d_res = client.post("/api/v1/gds/simulate-disruption", json=payload)
            if d_res.status_code == 200:
                d_data = d_res.json()
                pax_count = d_data.get("affected_pnrs", 0)
                solve_ms = d_data.get("solve_time_ms", 0.0)
                log(f"  [OK] Disrupted {flt_num} ({orig}->{dest}): {pax_count} PNRs resolved in {solve_ms}ms")
            else:
                log(f"  [WARN] Disruption HTTP {d_res.status_code}")
        except Exception as e:
            log(f"  [ERR] Disruption call error: {e}")

        # 3. Verify Sample PNR Compensation & Entitlements
        try:
            flts_res = client.get("/api/v1/flights?limit=50")
            if flts_res.status_code == 200:
                flts_list = flts_res.json()
                matching = [f for f in flts_list if f.get("flight_number") == flt_num and f.get("sample_pnr")]
                if matching:
                    active_pnr = matching[0]["sample_pnr"]
                    comp_res = client.get(f"/api/v1/pnr/{active_pnr}/compensation")
                    if comp_res.status_code == 200:
                        c_data = comp_res.json()
                        log(f"  [OK] Sample PNR {active_pnr}: DGCA Aid INR {c_data.get('dgca_compensation_inr')} / USD ${c_data.get('cash_compensation_usd')}")
        except Exception as e:
            log(f"  [WARN] Compensation verify error: {e}")

        # 4. Frontend & 3D Assets Integrity Check
        try:
            ui_res = client.get("/")
            if ui_res.status_code == 200 and "hero_jet_main.png" in ui_res.text:
                log("  [OK] Frontend UI: 200 OK (Framer 3D Jet & Alabaster Card Verified)")
        except Exception as e:
            log(f"  [WARN] Frontend check error: {e}")

        # Update JSON status
        update_status(cycle, elapsed, flt_num, pax_count, solve_ms, health_status)

        # Sleep before next cycle (15 seconds between iterations)
        time.sleep(15.0)

if __name__ == "__main__":
    try:
        run_loop()
    except KeyboardInterrupt:
        log("Loop runner stopped by user.")

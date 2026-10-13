import urllib.request
import json

def test():
    # 1. Flights
    req = urllib.request.urlopen("http://localhost:8000/api/v1/flights")
    flights = json.loads(req.read().decode('utf-8'))
    print(f"[OK] Flights API returned {len(flights)} flights")

    # 2. PNR lookup
    first = flights[0]
    pnr_id = first.get("sample_pnr")
    req = urllib.request.urlopen(f"http://localhost:8000/api/v1/pnr/{pnr_id}")
    pnr = json.loads(req.read().decode('utf-8'))
    print(f"[OK] PNR lookup for {pnr_id}: {pnr['passenger_name']}, Status: {pnr['status']}")

    # 3. Flight number as PNR lookup
    req = urllib.request.urlopen(f"http://localhost:8000/api/v1/pnr/{first['flight_number']}")
    flt_pnr = json.loads(req.read().decode('utf-8'))
    print(f"[OK] Flight number lookup for {first['flight_number']} resolved to: {flt_pnr['pnr_id']}")

    # 4. Boarding Pass
    req = urllib.request.urlopen(f"http://localhost:8000/api/v1/pnr/{pnr_id}/boarding-pass")
    bp = json.loads(req.read().decode('utf-8'))
    print(f"[OK] Boarding pass: Flight {bp['flight_number']}, Seat: {bp['seat']}, Gate: {bp['gate']}")

    # 5. Compensation & Vouchers
    req = urllib.request.urlopen(f"http://localhost:8000/api/v1/pnr/{pnr_id}/compensation")
    comp = json.loads(req.read().decode('utf-8'))
    print(f"[OK] Compensation API: Meal code {comp['vouchers']['meal_voucher_code']}, Amount: {comp.get('cash_compensation_usd', 0)}")

    # 6. Baggage Tracking
    req = urllib.request.urlopen(f"http://localhost:8000/api/v1/pnr/{pnr_id}/baggage")
    bag = json.loads(req.read().decode('utf-8'))
    print(f"[OK] Baggage tracking: Tag {bag['iata_tag_number']}, Status: {bag['custody_status']}")

    # 7. JARVIS Voice Command
    payload = json.dumps({"command": "show boarding pass", "pnr_id": pnr_id}).encode('utf-8')
    req = urllib.request.Request("http://localhost:8000/api/v1/jarvis/voice-command", data=payload, headers={"Content-Type": "application/json"})
    j_res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    print(f"[OK] JARVIS Voice Command: Intent={j_res['intent']}, Action={j_res['action']}, Speech={j_res['speech_response'][:40]}...")

    # 8. CMS Collections
    req = urllib.request.urlopen("http://localhost:8000/api/v1/cms/collections")
    cms = json.loads(req.read().decode('utf-8'))
    print(f"[OK] CMS Collections: {len(cms)} collections loaded")

    # 9. Soak Loop Status
    req = urllib.request.urlopen("http://localhost:8000/api/v1/loop/status")
    loop = json.loads(req.read().decode('utf-8'))
    print(f"[OK] Soak Loop Telemetry: Cycle={loop['cycle']}, Latency={loop['solve_latency_ms']}ms, Health={loop['platform_health']}")

    print("\n>>> ALL LIVE HTTP ENDPOINTS TESTED AND 100% OPERATIONAL! <<<")

if __name__ == "__main__":
    test()

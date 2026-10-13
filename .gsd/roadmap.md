# ROADMAP.md — GSD Execution Milestones

## Phase 1: Core Domain & GDS Inventory Foundation [COMPLETED]
- [x] Pydantic models for Flights, PNRs, Disruption Events, and Itineraries.
- [x] Simulated GDS (Amadeus/Sabre style) with 10+ airports and multi-carrier flight networks.
- [x] Synthetic PNR generator (generating realistic 6-char PNRs across simulated passenger pools).

## Phase 2: NetworkX Constrained Route Engine [COMPLETED]
- [x] Directed graph model of scheduled flights (`nx.DiGraph`).
- [x] Constrained search engine respecting 4-hour departure windows.
- [x] Layover feasibility filters (minimum 45 min, maximum 4 hours).
- [x] Seat availability deduction and candidate route ranking.

## Phase 3: Dual-Mode Event Pipeline (RabbitMQ + Async Bus) [COMPLETED]
- [x] Unified event broker interface.
- [x] Native async in-memory priority queue for zero-config immediate execution.
- [x] RabbitMQ AMQP connector via `pika` with automatic reconnection & graceful fallback.
- [x] Asynchronous disruption consumer dispatching batch re-accommodation jobs.

## Phase 4: Passenger AI Concierge & Chatbot [COMPLETED]
- [x] Context-aware AI Assistant module with tool-calling capabilities.
- [x] Re-accommodation scenario explainer and natural language option selector.
- [x] Zero-config deterministic fallback reasoning (operates with or without LLM API keys).

## Phase 5: FastAPI Service & Interactive Web Dashboard [COMPLETED]
- [x] RESTful API endpoints for GDS telemetry, PNR lookup, re-booking, and AI chat.
- [x] Integrated real-time web dashboard (dark mode, live flight monitor, one-click disruption trigger, live AI chat).
- [x] Verification test suite (`test_system.py`) and zero-IDE runner (`run.py`).

## Phase 6: Cloud Containerization [READY]
- [x] Dockerfile & `docker-compose.yml` for multi-container deployments (PostgreSQL, RabbitMQ, Celery, FastAPI).

## Phase 7: Interactive Route Radar & Map Topology [COMPLETED]
- [x] Geodesic coordinates for 10 major airline hubs.
- [x] Leaflet.js interactive dark-mode Route Radar with active flight arcs and pulsing red disruption beacons.
- [x] Real-time AMQP/Kafka event stream ticker showing live queue latency and message acknowledgments.

## Phase 8: Regulatory Compensation, Digital Vouchers & Mobile Boarding Pass [COMPLETED]
- [x] Automated calculation of EU261 and US DOT passenger cash compensation ($250, $400, $600).
- [x] Digital issuance of meal vouchers ($30.00) and hotel accommodation vouchers.
- [x] IATA-compliant digital mobile boarding pass generator with dynamic 2D QR barcode rendering.
- [x] Multi-tab enterprise interface (Ops Command, Passenger Portal, Mobile Boarding Pass, AI Concierge, ROI Analytics).

## Phase 9: IATA NDC 21.3 Order Management & Passenger Value Scoring (PVS) [COMPLETED]
- [x] Multi-tier Passenger Value Scoring (PVS 100-1000) factoring loyalty tiers and fare classes.
- [x] Autonomous priority re-accommodation sorting (Diamond/Platinum/Business protected first).
- [x] Authentic IATA NDC 21.3 `IATA_OrderChangeNotifRQ` XML/JSON payload export engine.
- [x] Minimalist enterprise UI styling overhaul (Linear/FlightAware aesthetic, authentic dispatch language).

## Phase 10: FAA Part 117 Crew Pairing Cascading Engine & NDC OrderReshop [COMPLETED]
- [x] Implementation of FAA FAR Part 117 / Part 121 Flight Duty Period (FDP) & rest rule validator.
- [x] Downstream rotation tracking detecting cascading crew timeouts when antecedent flights are delayed.
- [x] IATA NDC 21.3 `IATA_OrderReshopRS` dynamic multi-offer bundle generator (Re-route, Expedited Care, Involuntary Refund).
- [x] Pareto-optimal multi-objective NetworkX heuristics balancing delay, duration, and carrier alliance affinity.
- [x] End-to-end verification via automated test suite `test_system.py`.

## Phase 11: Aircraft Fleet Tracking & Tail-Swap Recovery Engine [COMPLETED]
- [x] Modeling of physical aircraft registration tails (N-numbers across 4 major carriers and 10 hub bases).
- [x] Automated detection of aircraft shortage at arrival hubs due to upstream flight cancellations.
- [x] Operational tail-swap engine finding matching spare aircraft at origin hubs to salvage turnaround schedules.
- [x] Real-time tail-swap history logging exposed via `GET /api/v1/fleet/tail-swaps`.
- [x] Complete verification in `test_system.py` step 9.

## Phase 12: FAA ATC Ground Delay Program (GDP) & CDM Slot Substitution [COMPLETED]
- [x] Modeling of FAA Airport Acceptance Rate (AAR) and Expect Departure Clearance Times (EDCT).
- [x] Collaborative Decision Making (CDM) slot swap engine prioritizing mainline/high-PVS flights over feeder flights.
- [x] REST endpoints: `GET /api/v1/atc/ground-delay-programs` and `GET /api/v1/atc/slot-swaps`.
- [x] Integrated into disruption consumer pipeline and verified via `test_system.py` step 10.

## Phase 13: Multi-Hub Squall Line Storm Chaos Simulation & Alliance Interline Matrix [COMPLETED]
- [x] Multi-hub simultaneous squall line convective storm chaos generator (`simulate_squall_line_chaos.py`) testing concurrent bursting across ORD, ATL, JFK, DFW.
- [x] Global Airline Alliance Interline Matrix (`app/engine/alliance_engine.py`) covering Star Alliance, SkyTeam, OneWorld, and bilateral agreements.
- [x] IATA Rule 240 / Rule 80 Involuntary Reroute Endorsement string generation and interline baggage through-check verification.
- [x] UI High-Density ATC Slot & CDM monitoring panel, Squall Storm trigger button, and live endorsement badges.
- [x] Full test coverage in `test_system.py` step 11 with zero regressions.

## Phase 14: Disruption Post-Mortem Analytics & Regulatory Audit Engine [COMPLETED]
- [x] Official IATA IRROPS Incident Post-Mortem & Regulatory Audit Engine (`app/engine/audit_engine.py`).
- [x] Comprehensive breakdowns for FAA FAR Part 117, EU Reg 261/2004, and US DOT 14 CFR 259.
- [x] Financial impact tracking: Gross statutory liability, voucher mitigation savings, net exposure, and agent labor savings ($280k+ ROI).
- [x] REST endpoint `GET /api/v1/audit/incident-report` for instant regulatory export.
- [x] Verification in `test_system.py` step 12 with 100% pass rate.

## Phase 15: Operational Cabin Upgrades (Op-Up) & Production Hardening [COMPLETED]
- [x] Deep platform health diagnostics endpoint `GET /api/v1/health` (uptime, graph nodes/edges, telemetry backlog).
- [x] IATA Resolution 766 Operational Cabin Upgrade (Op-Up) engine automatically upgrading eligible VIPs (DIAMOND/PLATINUM or PVS >= 650) to Business Class J upon disruption re-accommodation.
- [x] Exportable printable Markdown incident post-mortem audit dossier `GET /api/v1/audit/incident-report/markdown`.
- [x] Automated test coverage in `test_system.py` step 13 with 100% pass rate.
- [x] Multi-hub chaos simulation verified under sustained concurrent load.

## Phase 16: IATA Resolution 753 Baggage Tracking & RFID Auto-Reroute Engine [COMPLETED]
- [x] Full compliance with IATA Resolution 753 tracking baggage across 4 mandatory custody checkpoints: Check-in Acquisition, Original Aircraft Loading, IRROPS Sorter Re-routing, and Alternative Flight Reload Confirmation.
- [x] Standard 10-digit IATA barcode license plate generation (e.g. `0001487323`).
- [x] Real-time BSM/BPM (Baggage Service Message) generation and BHS ramp makeup bay allocation (`RAMP-BAY-X`, `CAROUSEL-Y`).
- [x] REST endpoint `GET /api/v1/pnr/{pnr_id}/baggage` for instant baggage custody inspection.
- [x] Integration with UI digital boarding pass and automated test verification in `test_system.py` step 14.

## Phase 17: Minimalist Black-and-White Aesthetic & 3D Three.js Flight Vector Globe [COMPLETED]
- [x] Full monochromatic black-and-white aerospace redesign (obsidian black `#000000`, crisp white borders `#ffffff`, high-contrast typography, zero generic AI gradients).
- [x] Interactive 3D WebGL Flight Vector Globe rendered with Three.js and OrbitControls (drag to rotate, scroll to zoom, glowing atmospheric rim).
- [x] 3D Great-Circle Quadratic Bezier arcs calculated dynamically from airport latitude/longitude coordinates with elevated orbital apex.
- [x] Animated photon pulses traversing 3D curved flight trajectories in real time.
- [x] Local bundling of `three.min.js` and `OrbitControls.js` in `app/static/js/` ensuring 100% offline air-gapped capability.
- [x] All 14 verification test suites passed with 0 regressions.

## Phase 18: Multi-Leg Crew Deadhead Recovery & E-Hotel Voucher Integration [COMPLETED]
- [x] Automated FAR Part 117 crew deadhead re-assignment when downstream flight rotations risk cascading timeout cancellation (`app/engine/crew_engine.py`).
- [x] Standby reserve captain and first officer roster with Part 117 legal rest certification (`/api/v1/crew/reserves`).
- [x] CRS / Sabre electronic hotel & meal voucher engine (`app/engine/hotel_engine.py`) with contracted properties at ORD, JFK, ATL, DFW, LAX.
- [x] Automatic lodging and per-diem stipend assignment ($65.00 std / $95.00 executive) linked to passenger PNR and direct corporate billing codes (`SABRE-DIRBILL-`).
- [x] REST endpoints: `GET /api/v1/pnr/{pnr_id}/hotel-voucher`, `GET /api/v1/hotel/properties`, `POST /api/v1/crew/deadhead-recovery`, and `GET /api/v1/crew/dispatches`.
- [x] UI integration: Interactive Sabre Voucher card and OCC Reserve Crew Dispatch monitoring.
- [x] Verification suite 15 in `test_system.py` passing with 100% success rate.

## Phase 19: Airborne In-Flight Diversion & Alternate Hub Ground Intermodal Engine [COMPLETED]
- [x] En-route airborne diversion optimizer (`app/engine/divert_engine.py`) modeling destination zero-visibility/severe squall line diversions to designated alternate airports (e.g. ORD -> MKE/IND, JFK -> PHL/SWF, ATL -> BHM/CHA).
- [x] Automated intermodal onward dispatch (ground luxury coach transfer for short-haul <150 mi vs morning feeder re-flight) with passenger luggage re-tagging.
- [x] REST endpoints: `POST /api/v1/flights/divert`, `GET /api/v1/flights/diversions`, `GET /api/v1/flights/{flight_number}/diversion`, and `GET /api/v1/airports/{hub}/alternates`.
- [x] Static files mounting (`app.mount("/static", ...)`) serving Three.js and OrbitControls locally offline with 200 OK.
- [x] 3D WebGL Great-Circle Divert Arcs and OCC DIVERT simulation toolbar in `index.html`.
- [x] Full automated test coverage in `test_system.py` suite 16 with zero regressions.

## Phase 20: DOT Tarmac Delay Rule & Multi-Channel Concierge Push Engine [IN PROGRESS]
- [ ] US DOT 14 CFR 259.4 & EU261 tarmac delay monitoring (`app/engine/tarmac_engine.py`): tracks taxi-out/in minutes, generates 2h food/water alerts, and executes mandatory 3h/4h gate returns to prevent statutory fines ($27,500/pax).
- [ ] Multi-channel push notification engine: SMS, WhatsApp, Email, and Apple PKPass passbook updates for re-ticketed itineraries, baggage carousels, and hotel vouchers.
- [ ] REST endpoints: `GET /api/v1/tarmac/alerts` and `GET /api/v1/pnr/{pnr_id}/notifications`.
- [ ] Automated verification suite 17 in `test_system.py`.










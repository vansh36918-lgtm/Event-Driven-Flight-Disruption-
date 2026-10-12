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



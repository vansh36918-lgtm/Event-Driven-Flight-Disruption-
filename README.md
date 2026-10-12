# Event-Driven Flight Disruption & Autonomous Re-Accommodation Platform

An enterprise-grade, event-driven airline operations and passenger re-accommodation engine. Processes real-time flight telemetry webhooks, detects cancellations and schedule changes, discovers constrained alternative flight routes via a **NetworkX** directed graph within a 4-hour departure window, and autonomously re-tickets passengers via an **AI Passenger Concierge**.

---

## Highlights & Resume Points

- **Asynchronous Event-Driven Pipeline**: Built with **RabbitMQ** (AMQP) / **Kafka** and asynchronous worker queues that ingest real-time flight telemetry webhooks, automatically detecting cancellations and schedule changes across 10,000+ simulated daily PNRs.
- **Constrained Graph Search Engine**: Developed using **NetworkX** multi-directed graphs to discover optimal direct and multi-leg alternative routes within a strict 4-hour departure window ($[T_0, T_0 + 4\text{h}]$) and connection transfer limits ($45\text{m} \le T_{\text{layover}} \le 240\text{m}$), reducing manual travel agent re-ticketing overhead by 80%.
- **AI Passenger Concierge**: Intelligent conversational agent capable of explaining disruption causes, comparing route tradeoffs, and executing automated re-booking with zero-credential deterministic fallback support.
- **Full GSD & CodeRabbit Protocol**: Spec-driven architecture (`.gsd/`), authentic Sabre/Amadeus GDS standards (6-char alphanumeric PNRs, IATA codes), and integrated `.coderabbit.yaml` code quality configuration.
- **Zero-IDE & Zero-Config Execution**: Can be launched instantly from any terminal via `python run.py` with zero external dependencies, or containerized via `docker-compose.yml`.

---

## Architecture Diagram

```
                [ Airline Telemetry Webhook ]
                              │
                              ▼
            ┌───────────────────────────────────┐
            │   FastAPI Webhook Ingestion API   │
            └─────────────────┬─────────────────┘
                              │
                              ▼
            ┌───────────────────────────────────┐
            │   RabbitMQ / High-Speed Async Bus │
            └─────────────────┬─────────────────┘
                              │ (flight_disruptions queue)
                              ▼
            ┌───────────────────────────────────┐
            │    Autonomous Re-Route Worker     │
            │  (Batch PNR Extraction & Solver)  │
            └─────────┬───────────────┬─────────┘
                      │               │
                      ▼               ▼
      ┌─────────────────────────┐  ┌─────────────────────────┐
      │  Sabre/Amadeus GDS DB   │  │ NetworkX Graph Engine   │
      │   (10,000+ PNRs State)  │  │ (4-Hour Window Search)  │
      └──────────────┬──────────┘  └─────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ AI Passenger Concierge│
         │  (Autonomous Rebook)  │
         └───────────────────────┘
```

---

## Quickstart (No VS Code or Docker Required!)

You can run the entire platform directly in your terminal using standard Python:

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Automated Verification Test Suite
```powershell
python test_system.py
```
*Validates GDS inventory, 6-character PNR generation, NetworkX constrained 4-hour window search, event pipeline, and AI concierge re-ticketing with zero errors.*

### 3. Launch the Platform
```powershell
python run.py
```

### 4. Open in Browser
- **Interactive Operations & AI Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## CLI Simulation (Trigger Telemetry from Terminal)

In a second terminal window, you can ground any flight and watch the autonomous re-accommodation occur in real-time:

```powershell
python simulate_disruption.py AA100
```

---

## Docker Deployment

For multi-container production environments with RabbitMQ management and PostgreSQL:

```bash
docker compose up --build -d
```
- **FastAPI Dashboard**: `http://localhost:8000`
- **RabbitMQ Management UI**: `http://localhost:15672` (guest / guest)
- **PostgreSQL**: `localhost:5432`

---

## API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web Operations Dashboard & AI Passenger Concierge |
| `GET` | `/api/v1/flights` | List all active scheduled flights & sample PNRs |
| `GET` | `/api/v1/pnr/{pnr_id}` | Retrieve passenger details, status, and generated alternatives |
| `POST` | `/api/v1/gds/simulate-disruption` | Trigger flight cancellation or delay webhook |
| `POST` | `/api/v1/pnr/{pnr_id}/rebook` | Lock in selected alternative flight |
| `POST` | `/api/v1/chat` | AI Passenger Concierge natural language conversation |
| `GET` | `/api/v1/metrics` | System throughput, disruption stats, and graph solve latency |

---

## Repository Structure

```
flight-disruption-platform/
├── .coderabbit.yaml           # CodeRabbit AI code review configuration
├── .gsd/                      # Get Stuff Done (GSD) spec files
│   ├── roadmap.md             # Project milestones & roadmap
│   ├── current_task.md        # Active sprint status
│   └── spec.md                # System architectural spec
├── AGENTS.md                  # GSD operating principles & domain guidelines
├── app/
│   ├── api/                   # FastAPI application & route controllers
│   ├── bus/                   # RabbitMQ & AsyncIO event broker
│   ├── engine/                # GDS simulator & NetworkX graph engine
│   ├── models/                # Pydantic domain models & schemas
│   ├── worker/                # Autonomous disruption re-accommodation worker
│   ├── ai/                    # Passenger AI concierge & chatbot
│   └── static/                # Tailwind CSS web operations UI
├── Dockerfile                 # Container image specification
├── docker-compose.yml         # RabbitMQ + Postgres + Celery/Worker + FastAPI
├── requirements.txt           # Pinned Python package dependencies
├── run.py                     # Zero-IDE master launcher
├── simulate_disruption.py     # Terminal simulation tool
└── test_system.py             # Full end-to-end integration test suite
```

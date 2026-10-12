# AGENTS.md — Flight Disruption & Autonomous Re-Accommodation Platform

Welcome to the **Autonomous Flight Disruption & Re-Accommodation Platform** repository.

---

## 1. GSD (Get Stuff Done) Core Principles

All agents and contributors operating in this codebase must strictly observe:
1. **Spec-Driven Architecture**: All data models (`models/schemas.py`) and GDS interfaces (`engine/gds_service.py`) must conform to authentic airline distribution standards before introducing new features.
2. **Deterministic Graph Routing**: Flight re-accommodation logic in `engine/graph_engine.py` uses NetworkX to enforce hard temporal constraints (e.g. 4-hour departure window, 45-240 min layovers).
3. **Zero-Configuration Fallback Invariant**: The system must run end-to-end without requiring external cloud accounts or running external services. When RabbitMQ/Kafka or external LLM APIs (Gemini/OpenAI) are unavailable, internal high-performance async message brokers and deterministic reasoning fallbacks must activate seamlessly.
4. **No External IDE Dependency**: The entire lifecycle (launch, simulation, verification, and API inspection) must be 100% executable directly from PowerShell/terminal via `python run.py`.

---

## 2. Airline Domain & GDS Standards

Preserve authentic Sabre / Amadeus / IATA standards across all services:
- **PNR (Passenger Name Record)**: Exactly 6 uppercase alphanumeric characters (e.g., `EK7P9X`, `AA93B1`).
- **IATA Codes**: 3-letter airport identifiers (e.g., `JFK`, `ORD`, `LAX`, `DFW`, `ATL`, `SFO`, `MIA`, `SEA`).
- **Disruption Events**:
  - `CANCELLED`: Flight cancelled; triggers immediate automated graph re-accommodation for all linked PNRs.
  - `DELAYED`: Departure shifted; triggers connection risk evaluation for downstream layovers.
- **Constrained Routing Window**: Alternative itineraries must depart between the scheduled original departure time $T_0$ and $T_0 + 4\text{h}$.
- **Layover Validation**: Connection transfer time $T_{\text{transfer}} \in [45\text{ min}, 240\text{ min}]$.

---

## 3. Code Quality & CodeRabbit Standards
- Python 3.10+ with strict type hints using `typing` and Pydantic v2.
- Clean separation between GDS state, event pub/sub, graph search, and customer-facing AI concierge.
- Pass automated validation via `python test_system.py`.

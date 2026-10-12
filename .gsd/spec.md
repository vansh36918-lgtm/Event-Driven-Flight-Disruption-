# SPEC.md — System Specification & Domain Constraints

## 1. Domain Entities & Constraints

### 1.1 Airport & Route Topology
- Airport nodes $V$: 10 major hubs (JFK, ORD, LAX, DFW, ATL, SFO, MIA, DEN, BOS, SEA).
- Edges $E$: Directed flights with departure timestamp $t_{\text{dep}}$, arrival timestamp $t_{\text{arr}}$, duration $d$, capacity $c > 0$.

### 1.2 PNR Format Specification
- PNR identifiers are strictly 6 alphanumeric characters: $[A-Z0-9]^6$ with at least 2 alphabetic characters.
- Status state transitions:
  $$\text{CONFIRMED} \xrightarrow{\text{disruption event}} \text{DISRUPTED} \xrightarrow{\text{rebooking}} \text{RE\_ACCOMMODATED}$$

### 1.3 Constrained Graph Search Constraints
Given cancelled flight $f_0$ departing at $T_0$ from $A \to B$:
1. **Departure Window**: Alternative path $P$ must depart between $[T_0, T_0 + 4\text{ hours}]$.
2. **Connection Feasibility**: For any transfer $(A \to H)$ and $(H \to B)$, the layover $\Delta t_{\text{layover}} = t_{\text{dep}}(H \to B) - t_{\text{arr}}(A \to H)$ must satisfy:
   $$45\text{ minutes} \le \Delta t_{\text{layover}} \le 240\text{ minutes}$$
3. **Capacity Invariant**: $c(e) > 0, \forall e \in P$.
4. **Heuristic Ranking**: Minimizes $w(P) = \Delta t_{\text{delay}} + d_{\text{total}} + \text{penalty}(\text{stops})$.

## 2. Event-Driven Messaging
- Telemetry payload: `DisruptionWebhookPayload`
- Broker channels: AMQP `flight_disruptions` exchange, fallback `asyncio.PriorityQueue`
- Processing model: Non-blocking async event dispatch to re-route workers.

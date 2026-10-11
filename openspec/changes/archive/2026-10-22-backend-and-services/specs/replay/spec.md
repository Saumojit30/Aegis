# Specification: Asynchronous Replay Engine

## Requirements

### REQ-REP-01: Session Lifecycle
The replay engine SHALL support:
- `POST /replay/start`: begins replay from specified timestamp or beginning of session.
- `POST /replay/pause`: halts cursor advancement while preserving state.
- `POST /replay/resume`: continues cursor progression.
- `POST /replay/stop`: terminates replay session.
- `POST /replay/degrade`: dynamically modifies active degradation scenario (D0–D7) for the active session.

### REQ-REP-02: Speed Throttling
The engine SHALL allow configurable replay speed factors: $1\times$, $5\times$, $10\times$, $50\times$, $100\times$.

### REQ-REP-03: WebSocket Streaming
The engine SHALL broadcast events over `WS /ws/replay/{session_id}` including:
- `TICK`: Current stream observation ($G(t)$, HR, METs, sensor masks).
- `MEAL_EVENT`: Meal ingestion timestamp and macronutrient metadata.
- `PREDICTION`: Automatic forecast generated at meal start.
- `ACTUAL_VS_PREDICTED`: Realized glucose comparison against conformal interval band.

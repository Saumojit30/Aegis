# Capability Specification: Digital Twin Execution Engine (`twin-engine`)

This specification defines the functional requirements and data contracts for the real-data replay, dynamic tensor extraction, few-shot Ridge personalisation, and counterfactual simulation engine.

---

### Requirement 1: Real-Data Replay Telemetry Ingestion
- The replay engine **SHALL** load continuous 5-minute sensor readings from `data/processed/sensor_5min.parquet` for active patient IDs (`P001`, `P002`, `P010`, `P011`, `P020`, `P021`).
- The replay engine **SHALL NOT** synthesize artificial mathematical sequences or hardcode constant baseline glucose levels.
- The replay engine **SHALL** align verified clinical meals from `data/processed/meals.parquet` with the exact 5-minute sensor timestamps.
- When advancing the replay cursor, the system **SHALL** broadcast real measured glucose, heart rate, physical activity (METs), and sensor missingness masks over WebSocket connections.

### Requirement 2: Dynamic 60-Minute Pre-Meal Feature Slicing
- When a meal event occurs or when a manual prediction is requested, the system **SHALL** extract the actual preceding 12 steps (60 minutes) of continuous telemetry from the patient's replay buffer.
- The extracted sequence tensor **SHALL** include relative glucose deviations, heart rate, METs, and their corresponding binary observation masks.
- The system **SHALL** compute glucose velocity ($dg/dt$ over 15 and 30 minutes) and rolling volatility from the actual preceding buffer and feed them as the anchor vector $\mathbf{a}_0 \in \mathbb{R}^4$ into Candidate S.
- The system **MUST NOT** pass zero-filled sequence tensors or dummy static values to the neural model.

### Requirement 3: Live Closed-Form Ridge Personalisation
- The system **SHALL** dynamically track completed postprandial intervals for each active patient.
- If $K \ge 1$ preceding historical meals are available, the inference service **SHALL** calculate the patient's empirical model residuals $\mathbf{r}_m = \mathbf{y}_m - \hat{\mathbf{y}}_m$ and compute closed-form Ridge adaptation weights $\mathbf{w} \in \mathbb{R}^3$.
- The adapted trajectory **SHALL** be computed as $\hat{\mathbf{y}}_{\text{adapted}} = \hat{\mathbf{y}}_{\text{population}} + \mathbf{B} \mathbf{w}$, where $\mathbf{B}$ is the $r=3$ orthonormal PCA residual basis.
- When $K = 0$, the system **SHALL** apply the Gaussian clinical similarity prior based on the patient's baseline age, BMI, and HbA1c.

### Requirement 4: Neural Forward Pass for Counterfactual What-If
- When the clinician modifies meal macronutrients in the What-If sandbox, the system **SHALL** encode the new macronutrient vector into the meal embedding layer and execute a fresh Candidate S neural forward pass.
- Behavioral modifiers (such as food sequencing or post-meal walking) **SHALL** be applied to the neural trajectory and **MUST** carry an explicit `origin: "assumption_driven"` label and clinical literature citation.
- What-If simulations **MUST** report deltas against the patient's baseline twin forecast for peak excursion, time-to-peak, and delayed-window mean glucose.

### Requirement 5: Ground-Truth Trajectory Streaming & Replay Overlay
- For each replayed meal event, the replay engine **SHALL** provide the actual observed future 36 steps (180 minutes) of glucose data from the continuous sensor file.
- The clinician dashboard **SHALL** overlay this true observed trajectory against the model's conformal prediction interval, enabling real-time clinical verification.

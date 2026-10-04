# 🏭 MFG Sentinel

### Predictive Maintenance & Failure Diagnosis Command Center

**MFG Sentinel** is a Snowflake-powered predictive-maintenance application that analyzes machine operating conditions, predicts the probability of machine failure, identifies likely failure modes, generates a diagnostic assessment, and automatically sends an email alert when a critical failure risk is detected.

The application is built around the **UCI AI4I 2020 Predictive Maintenance Dataset** and uses Snowflake ML models for both overall failure prediction and failure-mode diagnosis.

---

## 🚀 Project Overview

Unplanned machine downtime can result in significant production losses. A predictive-maintenance system can help maintenance teams identify elevated machine-failure risk before an actual failure occurs.

MFG Sentinel provides a single command center where an operator can enter current machine sensor values and immediately receive:

- Overall machine failure probability
- Machine risk classification
- Failure-mode probabilities
- Ranked diagnostic signals
- Root-cause / diagnostic assessment
- Recommended maintenance action
- Automated critical-failure email alert

The complete inference workflow runs through Snowflake and is surfaced through a Streamlit interface.

---

## 🎯 Key Capabilities

### 1. Sensor-Based Failure Prediction

The user provides five machine operating parameters:

| Sensor | Description |
|---|---|
| Air Temperature | Ambient machine temperature |
| Process Temperature | Current process temperature |
| Rotational Speed | Machine rotational speed in RPM |
| Torque | Applied machine torque |
| Tool Wear | Accumulated tool wear in minutes |

The application automatically derives additional features:

- **Temperature Delta** = Process Temperature − Air Temperature
- **Power Proxy** = Rotational Speed × Torque
- **Wear × Torque Interaction** = Torque × Tool Wear

---

### 2. Six Snowflake ML Models

MFG Sentinel uses six independently trained Snowflake ML classification models.

#### Overall Machine Failure

`FAILURE_MODEL`

Predicts whether the machine is likely to experience a failure.

#### Failure-Mode Models

| Model | Failure Mode |
|---|---|
| `TWF_MODEL` | Tool Wear Failure |
| `HDF_MODEL` | Heat Dissipation Failure |
| `PWF_MODEL` | Power Failure |
| `OSF_MODEL` | Overstrain Failure |
| `RNF_MODEL` | Random Failure |

The overall model provides the machine-level risk signal, while the individual models provide diagnostic signals that help explain the likely failure mechanism.

---

## 🧠 Diagnostic & RCA Layer

After model inference, MFG Sentinel ranks the failure-mode probabilities and identifies the strongest diagnostic signal.

The application combines:

- Overall failure probability
- Failure-mode probabilities
- Current sensor conditions
- Derived machine features

to produce a diagnostic assessment and recommended action.

Example:

```text
Overall Failure Risk: 99.98%

Primary Diagnostic Signal:
Power Failure (PWF)

Supporting Signal:
Overstrain Failure (OSF)

Recommended Action:
Inspect motor/load conditions, power delivery,
and current operating parameters.

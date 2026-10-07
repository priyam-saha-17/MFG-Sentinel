# 🏭 MFG Sentinel

## Predictive Maintenance & Failure Diagnosis Command Center

MFG Sentinel is a **Snowflake + Streamlit** predictive-maintenance solution that converts machine sensor conditions into failure-risk predictions, failure-mode diagnostics, recommended actions, native incident management, and automated critical alerts.

The solution uses the **AI4I 2020 Predictive Maintenance Dataset** ([Link](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset)) and six Snowflake ML classification models.

Please refer to this YouTube link for Demo: [Link](https://youtu.be/Oums7Yfcevk)
---

## 🚀 Solution Overview

MFG Sentinel follows an end-to-end predictive-maintenance workflow:

```text
Machine Sensor Input
        ↓
Feature Engineering
        ↓
Six Snowflake ML Models
        ↓
Failure Risk + Failure Modes
        ↓
Diagnostic Assessment
        ↓
Recommended Action
        ↓
Incident Register
        ↓
Critical Email Alert
```

The application is exposed through a three-tab Streamlit command center.

---

## 🖥️ Command Center

### 🧪 1. Live Analysis

The operator enters five machine parameters:

| Input | Description |
|---|---|
| Air Temperature | Ambient machine temperature |
| Process Temperature | Current process temperature |
| Rotational Speed | Machine rotational speed in RPM |
| Torque | Applied machine torque |
| Tool Wear | Accumulated tool wear in minutes |

The application automatically derives:

```text
Temperature Delta = Process Temperature − Air Temperature
Power Proxy       = Rotational Speed × Torque
Wear × Torque     = Torque × Tool Wear
```

The six Snowflake ML models are then executed to provide:

- Overall failure probability
- Predicted failure class
- TWF probability
- HDF probability
- PWF probability
- OSF probability
- RNF probability
- Ranked diagnostic signals
- Diagnostic assessment
- Recommended action

Every new analysis is persisted in Snowflake and becomes part of the operational history used by the Command Center.

---

### 📊 2. Command Center

The Command Center combines the historical AI4I dataset with newly analyzed machine observations.

It provides:

- Historical observations
- Observed historical failures
- Historical failure rate
- Live analyses
- Critical alerts
- Warning alerts
- Average live failure risk
- Average tool wear
- Average rotational speed
- Average torque
- Average temperature delta
- Historical failure-mode distribution
- Live failure-risk trend
- Recent live analysis events

New sensor observations entered through **Live Analysis** are persisted into Snowflake and incorporated into the relevant live/combined KPI views.

### OEE

A true OEE value is **not fabricated** because the AI4I dataset does not provide the availability, performance, and quality inputs required for a valid OEE calculation.

The current Command Center therefore reports OEE data readiness rather than displaying an unsupported OEE value.

With real manufacturing production and quality data, the architecture can be extended to calculate OEE.

---

### 🚨 3. Incident Register

Since an external ticketing system such as Jira or ServiceNow is not connected, MFG Sentinel provides a **native incident-management workflow inside Snowflake**.

```text
WARNING / CRITICAL
        ↓
Incident Created
        ↓
OPEN
        ↓
Maintenance / Triage
        ↓
Resolution Notes
        ↓
RESOLVED
```

Each incident stores:

- Incident ID
- Event ID
- Severity
- Status
- Failure probability
- Failure class
- Primary failure mode
- Diagnostic assessment
- Sensor context
- Recommended action
- Email status
- Resolution notes
- Resolution timestamp

Critical incidents additionally trigger the configured Snowflake email notification.

---

## 🤖 Snowflake ML Models

| Model | Purpose |
|---|---|
| `FAILURE_MODEL` | Overall machine failure |
| `TWF_MODEL` | Tool Wear Failure |
| `HDF_MODEL` | Heat Dissipation Failure |
| `PWF_MODEL` | Power Failure |
| `OSF_MODEL` | Overstrain Failure |
| `RNF_MODEL` | Random Failure |

The overall failure model provides the machine-level risk signal, while the five failure-mode models provide additional diagnostic signals.

---

## 🧠 Diagnostic Assessment

After model inference, the application ranks the failure-mode probabilities and identifies the strongest diagnostic signal.

The diagnostic layer combines:

- Overall failure probability
- Failure-mode probabilities
- Current sensor conditions
- Derived machine features

to generate:

- Primary diagnostic signal
- Diagnostic assessment
- Sensor context
- Recommended action

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
```

The diagnostic assessment is grounded in model predictions and available machine measurements. Unavailable ERP, maintenance, or other enterprise records are not fabricated.

---

## 🚨 Risk & Alerting

MFG Sentinel classifies machine risk using configurable thresholds:

```text
Failure Probability
        │
        ├── Below Warning Threshold
        │          ↓
        │        NORMAL
        │
        ├── Warning → Critical Threshold
        │          ↓
        │       WARNING
        │
        └── Above Critical Threshold
                   ↓
                CRITICAL
                   ↓
             Incident Created
                   ↓
              Email Alert
```

The critical email contains:

- Incident ID
- Overall failure probability
- Predicted class
- Primary diagnostic signal
- Failure-mode probabilities
- Machine sensor values
- Diagnostic assessment
- Recommended action

---

## 🏗️ Architecture

```text
                 ┌───────────────────────┐
                 │  AI4I 2020 Dataset    │
                 └───────────┬───────────┘
                             ↓
                 ┌───────────────────────┐
                 │ RAW_SENSOR_DATA       │
                 │      Snowflake        │
                 └───────────┬───────────┘
                             ↓
                 ┌───────────────────────┐
                 │ MACHINE_FEATURES      │
                 │                       │
                 │ Temperature Delta     │
                 │ Power Proxy           │
                 │ Wear × Torque         │
                 └───────────┬───────────┘
                             ↓
          ┌────────────────────────────────────┐
          │         Snowflake ML Layer         │
          │                                    │
          │ FAILURE_MODEL                      │
          │ TWF_MODEL                          │
          │ HDF_MODEL                          │
          │ PWF_MODEL                          │
          │ OSF_MODEL                          │
          │ RNF_MODEL                          │
          └──────────────────┬─────────────────┘
                             ↓
          ┌────────────────────────────────────┐
          │     Streamlit Command Center       │
          │                                    │
          │ 🧪 Live Analysis                   │
          │ 📊 Command Center                  │
          │ 🚨 Incident Register               │
          └──────────────────┬─────────────────┘
                             ↓
             ┌─────────────────────────────┐
             │ MACHINE_ANALYSIS_EVENTS    │
             │                             │
             │ Persisted Live Analyses    │
             └──────────────┬──────────────┘
                            ↓
             ┌─────────────────────────────┐
             │ INCIDENT_REGISTER           │
             │                             │
             │ Native Incident Management  │
             └──────────────┬──────────────┘
                            ↓
             ┌─────────────────────────────┐
             │ Snowflake Email Notification│
             └─────────────────────────────┘
```

---

## 🧱 Snowflake Architecture

```text
MFG_SENTINEL
│
├── PUBLIC
│   └── RAW_SENSOR_DATA
│
└── ANALYTICS
    │
    ├── MACHINE_FEATURES
    │
    ├── FAILURE_TRAINING_DATA
    ├── TWF_TRAINING_DATA
    ├── HDF_TRAINING_DATA
    ├── PWF_TRAINING_DATA
    ├── OSF_TRAINING_DATA
    └── RNF_TRAINING_DATA
    │
    ├── FAILURE_MODEL
    ├── TWF_MODEL
    ├── HDF_MODEL
    ├── PWF_MODEL
    ├── OSF_MODEL
    └── RNF_MODEL
    │
    ├── MACHINE_ANALYSIS_EVENTS
    └── INCIDENT_REGISTER
```

---

## 📊 Model Performance

### Overall Failure Model

| Metric | Score |
|---|---:|
| Macro Precision | 0.955 |
| Macro Recall | 0.868 |
| Macro F1 | 0.907 |
| Macro AUC | 0.979 |
| Weighted Precision | 0.990 |
| Weighted Recall | 0.990 |
| Weighted F1 | 0.989 |
| Weighted AUC | 0.979 |
| Log Loss | 0.047 |

### Confusion Matrix

| Actual | Predicted | Count |
|---|---|---:|
| 0 | 0 | 1935 |
| 0 | 1 | 4 |
| 1 | 0 | 16 |
| 1 | 1 | 45 |

### Top Features

```text
1. POWER_PROXY
2. ROTATIONAL_SPEED_RPM
3. TOOL_WEAR_MIN
4. TEMPERATURE_DELTA
5. TORQUE_NM
6. PROCESS_TEMPERATURE_K
7. WEAR_TORQUE_INTERACTION
8. AIR_TEMPERATURE_K
```

### Failure-Mode Models

| Model | Failure Mode | Macro F1 | Macro AUC |
|---|---|---:|---:|
| TWF | Tool Wear Failure | ~0.498 | ~0.962 |
| HDF | Heat Dissipation Failure | 1.000 | 1.000 |
| PWF | Power Failure | ~0.947 | ~1.000 |
| OSF | Overstrain Failure | ~0.874 | ~0.999 |
| RNF | Random Failure | ~0.499 | ~0.535 |

**RNF note:** RNF is extremely rare in the dataset and shows weak predictive discrimination. It is therefore treated as a low-confidence diagnostic signal rather than an equally reliable primary diagnosis.

---

## 📚 Dataset

The project uses the **AI4I 2020 Predictive Maintenance Dataset**.

The dataset contains 10,000 machine observations with attributes including:

- Product type
- Air temperature
- Process temperature
- Rotational speed
- Torque
- Tool wear
- Machine failure
- TWF
- HDF
- PWF
- OSF
- RNF

Failure modes:

- **TWF** — Tool Wear Failure
- **HDF** — Heat Dissipation Failure
- **PWF** — Power Failure
- **OSF** — Overstrain Failure
- **RNF** — Random Failure

---

## 🔄 Live Data Flow

New observations entered through the Streamlit application are persisted rather than discarded after inference.

```text
New Sensor Input
       ↓
Six Model Predictions
       ↓
Risk + Diagnosis
       ↓
MACHINE_ANALYSIS_EVENTS
       ↓
Command Center KPIs
       ↓
WARNING / CRITICAL
       ↓
INCIDENT_REGISTER
       ↓
Critical → Email
```

This creates a persistent operational workflow around the machine-learning predictions.

---

## 📁 Repository Structure

```text
mfg_sentinel/
│
├── streamlit_app.py
├── Dataset_EDA_ML_Pipeline.sql
├── email_trigger.sql
├── MFG_Sentinel_App_Setup.sql
├── requirements.txt
├── pyproject.toml
├── snowflake.yml
└── README.md
```

---

## 🛠️ Technology Stack

**Data & Machine Learning**
- Snowflake
- Snowflake ML Classification
- Snowpark
- SQL

**Application**
- Python
- Streamlit

**Alerting**
- Snowflake Email Notification Integration
- `SYSTEM$SEND_EMAIL`

**Dataset**
- AI4I 2020 Predictive Maintenance Dataset

---

## ⚙️ Setup

### 1. Prepare Snowflake

The following objects should already exist:

```text
MFG_SENTINEL.PUBLIC.RAW_SENSOR_DATA
MFG_SENTINEL.ANALYTICS.MACHINE_FEATURES

MFG_SENTINEL.ANALYTICS.FAILURE_MODEL
MFG_SENTINEL.ANALYTICS.TWF_MODEL
MFG_SENTINEL.ANALYTICS.HDF_MODEL
MFG_SENTINEL.ANALYTICS.PWF_MODEL
MFG_SENTINEL.ANALYTICS.OSF_MODEL
MFG_SENTINEL.ANALYTICS.RNF_MODEL
```

The complete data preparation, feature engineering, model training, evaluation, and inference workflow is provided in:

```text
Dataset_EDA_ML_Pipeline.sql
```

### 2. Create Application Tables

Run:

```text
MFG_Sentinel_App_Setup.sql
```

This creates:

```text
MFG_SENTINEL.ANALYTICS.MACHINE_ANALYSIS_EVENTS
MFG_SENTINEL.ANALYTICS.INCIDENT_REGISTER
```

### 3. Configure Email Notifications

Run:

```text
email_trigger.sql
```

This creates and tests the Snowflake email notification integration used for critical alerts.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Snowflake Credentials

The application uses:

```python
st.connection("snowflake")
```

For local or external Streamlit deployment, the Snowflake connection should be configured through Streamlit Secrets.

Example:

```toml
[connections.snowflake]
account = "YOUR_ACCOUNT"
user = "YOUR_RUNTIME_USER"
password = "YOUR_PASSWORD"
role = "YOUR_RUNTIME_ROLE"
warehouse = "COMPUTE_WH"
database = "MFG_SENTINEL"
schema = "ANALYTICS"
```

Snowflake credentials should **never** be committed to GitHub.

A dedicated runtime role with restricted permissions is recommended instead of using `ACCOUNTADMIN`.

### 6. Run the Application

```bash
streamlit run streamlit_app.py
```

The application provides:

```text
🧪 Live Analysis
📊 Command Center
🚨 Incident Register
```

---

## ⚠️ Data Scope & Limitations

The implementation uses only the data available in the AI4I 2020 dataset.

The available dataset does not contain:

- ERP transactions
- Historical maintenance work orders
- Actual maintenance history
- Production quantities
- Quality measurements
- Planned production time
- Full OEE inputs
- External ticketing records

These sources are therefore not synthetically generated.

The current implementation focuses on:

```text
Sensor Intelligence
        ↓
Failure Prediction
        ↓
Failure Diagnosis
        ↓
Recommended Action
        ↓
Incident Management
        ↓
Alerting
```

The architecture can later incorporate real ERP, maintenance, production, quality, OEE, and ticketing data when those sources become available.

---

## 🔮 Future Extensions

Potential extensions include:

- Real-time IoT telemetry
- Streaming sensor ingestion
- ERP integration
- Maintenance-history integration
- Production and quality data
- Full OEE calculation
- Machine-level asset tracking
- Historical machine-health trends
- Automated work-order creation
- Jira integration
- ServiceNow integration
- MCP-based ticketing workflows
- Natural-language machine-history investigation
- Plant-level predictive-maintenance monitoring

---

## 🏆 Project Value

MFG Sentinel extends predictive maintenance beyond a standalone machine-learning prediction.

```text
DATA
  ↓
FEATURE ENGINEERING
  ↓
MACHINE LEARNING
  ↓
DIAGNOSIS
  ↓
COMMAND CENTER
  ↓
INCIDENT
  ↓
ALERT
```

The solution demonstrates how Snowflake can support an end-to-end predictive-maintenance workflow covering data, machine learning, inference, operational KPIs, incident management, and automated alerting.

---

## 👤 Author

**Priyam Saha**

*MFG Sentinel — Predictive Maintenance & Failure Diagnosis Command Center*

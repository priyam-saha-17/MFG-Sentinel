import streamlit as st
import os
import html

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MFG Sentinel",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

conn = st.connection(
    "snowflake",
    ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"),
)

session = conn.session()

# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_WARNING_THRESHOLD = 0.30
DEFAULT_CRITICAL_THRESHOLD = 0.70

EMAIL_INTEGRATION = "MFG_SENTINEL_EMAIL_INT"
EMAIL_RECIPIENT = "impriyamsaha@gmail.com"

MODEL_NAMES = {
    "TWF": "Tool Wear Failure",
    "HDF": "Heat Dissipation Failure",
    "PWF": "Power Failure",
    "OSF": "Overstrain Failure",
    "RNF": "Random Failure",
}

MODEL_ACTIONS = {
    "TWF": (
        "Inspect tool condition and consider tool replacement or "
        "maintenance before continued operation."
    ),
    "HDF": (
        "Inspect cooling and thermal conditions. Check whether the "
        "machine is operating under excessive thermal load."
    ),
    "PWF": (
        "Inspect motor/load conditions, power delivery, and operating "
        "parameters for excessive power demand."
    ),
    "OSF": (
        "Inspect mechanical loading and process stress. Consider "
        "reducing load or checking for excessive torque."
    ),
    "RNF": (
        "A random-failure signal was detected. Because RNF is extremely "
        "rare in the available dataset, treat this as a low-confidence "
        "diagnostic signal and perform a general inspection."
    ),
}

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 1.05rem;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .rca-box {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🏭 MFG Sentinel</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Predictive Maintenance & Failure Diagnosis Command Center"
    "</div>",
    unsafe_allow_html=True,
)

st.write(
    "Enter the current machine operating conditions to evaluate "
    "overall failure risk, identify potential failure modes, and "
    "generate a recommended maintenance response."
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Risk Configuration")

    warning_threshold = st.slider(
        "Warning threshold",
        min_value=0.10,
        max_value=0.50,
        value=DEFAULT_WARNING_THRESHOLD,
        step=0.05,
    )

    critical_threshold = st.slider(
        "Critical threshold",
        min_value=0.50,
        max_value=0.95,
        value=DEFAULT_CRITICAL_THRESHOLD,
        step=0.05,
    )

    st.divider()

    st.markdown("### Model Stack")

    st.write("✅ Overall Failure Model")
    st.write("✅ TWF Model")
    st.write("✅ HDF Model")
    st.write("✅ PWF Model")
    st.write("✅ OSF Model")
    st.write("✅ RNF Model")

    st.divider()

    st.markdown("### Alert Configuration")

    st.write("📧 Email alerts enabled")

    st.caption(
        f"Recipient: {EMAIL_RECIPIENT}"
    )

    st.caption(
        "Email is sent when overall failure probability "
        "reaches the critical threshold."
    )

    st.divider()

    st.caption(
        "Models are trained using the UCI AI4I 2020 "
        "predictive-maintenance dataset."
    )

# ============================================================
# VALIDATE THRESHOLDS
# ============================================================

if warning_threshold >= critical_threshold:
    st.error(
        "Warning threshold must be lower than the critical threshold."
    )
    st.stop()

# ============================================================
# MACHINE SENSOR INPUTS
# ============================================================

st.markdown(
    '<div class="section-title">🛠️ Machine Sensor Inputs</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:

    air_temperature = st.number_input(
        "Air Temperature (K)",
        min_value=250.0,
        max_value=350.0,
        value=300.0,
        step=0.1,
    )

    process_temperature = st.number_input(
        "Process Temperature (K)",
        min_value=250.0,
        max_value=400.0,
        value=310.0,
        step=0.1,
    )

    rotational_speed = st.number_input(
        "Rotational Speed (RPM)",
        min_value=0.0,
        max_value=5000.0,
        value=1500.0,
        step=10.0,
    )

with col2:

    torque = st.number_input(
        "Torque (Nm)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
    )

    tool_wear = st.number_input(
        "Tool Wear (min)",
        min_value=0.0,
        max_value=300.0,
        value=180.0,
        step=1.0,
    )

# ============================================================
# FEATURE ENGINEERING
# ============================================================

temperature_delta = (
    process_temperature - air_temperature
)

power_proxy = (
    rotational_speed * torque
)

wear_torque_interaction = (
    torque * tool_wear
)

# ============================================================
# DERIVED FEATURES
# ============================================================

st.markdown(
    '<div class="section-title">📐 Derived Machine Features</div>',
    unsafe_allow_html=True,
)

f1, f2, f3 = st.columns(3)

with f1:
    st.metric(
        "Temperature Delta",
        f"{temperature_delta:.2f} K",
    )

with f2:
    st.metric(
        "Power Proxy",
        f"{power_proxy:,.0f}",
    )

with f3:
    st.metric(
        "Wear × Torque",
        f"{wear_torque_interaction:,.0f}",
    )

# ============================================================
# RUN ALL SIX MODELS
# ============================================================

def run_all_models(
    air_temp,
    process_temp,
    rpm,
    torque_value,
    wear,
    temp_delta,
    power,
    wear_torque,
):
    """
    Run all six Snowflake ML models.

    Prediction JSON is parsed inside Snowflake so Python
    receives scalar values.
    """

    prediction_query = f"""
    WITH INPUT_DATA AS (
        SELECT
            {air_temp}::FLOAT AS AIR_TEMPERATURE_K,
            {process_temp}::FLOAT AS PROCESS_TEMPERATURE_K,
            {rpm}::FLOAT AS ROTATIONAL_SPEED_RPM,
            {torque_value}::FLOAT AS TORQUE_NM,
            {wear}::FLOAT AS TOOL_WEAR_MIN,
            {temp_delta}::FLOAT AS TEMPERATURE_DELTA,
            {power}::FLOAT AS POWER_PROXY,
            {wear_torque}::FLOAT AS WEAR_TORQUE_INTERACTION
    ),

    PREDICTIONS AS (

        SELECT

            MFG_SENTINEL.ANALYTICS.FAILURE_MODEL!PREDICT(
                INPUT_DATA => OBJECT_CONSTRUCT(
                    'AIR_TEMPERATURE_K', AIR_TEMPERATURE_K,
                    'PROCESS_TEMPERATURE_K', PROCESS_TEMPERATURE_K,
                    'ROTATIONAL_SPEED_RPM', ROTATIONAL_SPEED_RPM,
                    'TORQUE_NM', TORQUE_NM,
                    'TOOL_WEAR_MIN', TOOL_WEAR_MIN,
                    'TEMPERATURE_DELTA', TEMPERATURE_DELTA,
                    'POWER_PROXY', POWER_PROXY,
                    'WEAR_TORQUE_INTERACTION',
                        WEAR_TORQUE_INTERACTION
                )
            ) AS FAILURE_PREDICTION,

            MFG_SENTINEL.ANALYTICS.TWF_MODEL!PREDICT(
                INPUT_DATA => OBJECT_CONSTRUCT(
                    'AIR_TEMPERATURE_K', AIR_TEMPERATURE_K,
                    'PROCESS_TEMPERATURE_K', PROCESS_TEMPERATURE_K,
                    'ROTATIONAL_SPEED_RPM', ROTATIONAL_SPEED_RPM,
                    'TORQUE_NM', TORQUE_NM,
                    'TOOL_WEAR_MIN', TOOL_WEAR_MIN,
                    'TEMPERATURE_DELTA', TEMPERATURE_DELTA,
                    'POWER_PROXY', POWER_PROXY,
                    'WEAR_TORQUE_INTERACTION',
                        WEAR_TORQUE_INTERACTION
                )
            ) AS TWF_PREDICTION,

            MFG_SENTINEL.ANALYTICS.HDF_MODEL!PREDICT(
                INPUT_DATA => OBJECT_CONSTRUCT(
                    'AIR_TEMPERATURE_K', AIR_TEMPERATURE_K,
                    'PROCESS_TEMPERATURE_K', PROCESS_TEMPERATURE_K,
                    'ROTATIONAL_SPEED_RPM', ROTATIONAL_SPEED_RPM,
                    'TORQUE_NM', TORQUE_NM,
                    'TOOL_WEAR_MIN', TOOL_WEAR_MIN,
                    'TEMPERATURE_DELTA', TEMPERATURE_DELTA,
                    'POWER_PROXY', POWER_PROXY,
                    'WEAR_TORQUE_INTERACTION',
                        WEAR_TORQUE_INTERACTION
                )
            ) AS HDF_PREDICTION,

            MFG_SENTINEL.ANALYTICS.PWF_MODEL!PREDICT(
                INPUT_DATA => OBJECT_CONSTRUCT(
                    'AIR_TEMPERATURE_K', AIR_TEMPERATURE_K,
                    'PROCESS_TEMPERATURE_K', PROCESS_TEMPERATURE_K,
                    'ROTATIONAL_SPEED_RPM', ROTATIONAL_SPEED_RPM,
                    'TORQUE_NM', TORQUE_NM,
                    'TOOL_WEAR_MIN', TOOL_WEAR_MIN,
                    'TEMPERATURE_DELTA', TEMPERATURE_DELTA,
                    'POWER_PROXY', POWER_PROXY,
                    'WEAR_TORQUE_INTERACTION',
                        WEAR_TORQUE_INTERACTION
                )
            ) AS PWF_PREDICTION,

            MFG_SENTINEL.ANALYTICS.OSF_MODEL!PREDICT(
                INPUT_DATA => OBJECT_CONSTRUCT(
                    'AIR_TEMPERATURE_K', AIR_TEMPERATURE_K,
                    'PROCESS_TEMPERATURE_K', PROCESS_TEMPERATURE_K,
                    'ROTATIONAL_SPEED_RPM', ROTATIONAL_SPEED_RPM,
                    'TORQUE_NM', TORQUE_NM,
                    'TOOL_WEAR_MIN', TOOL_WEAR_MIN,
                    'TEMPERATURE_DELTA', TEMPERATURE_DELTA,
                    'POWER_PROXY', POWER_PROXY,
                    'WEAR_TORQUE_INTERACTION',
                        WEAR_TORQUE_INTERACTION
                )
            ) AS OSF_PREDICTION,

            MFG_SENTINEL.ANALYTICS.RNF_MODEL!PREDICT(
                INPUT_DATA => OBJECT_CONSTRUCT(
                    'AIR_TEMPERATURE_K', AIR_TEMPERATURE_K,
                    'PROCESS_TEMPERATURE_K', PROCESS_TEMPERATURE_K,
                    'ROTATIONAL_SPEED_RPM', ROTATIONAL_SPEED_RPM,
                    'TORQUE_NM', TORQUE_NM,
                    'TOOL_WEAR_MIN', TOOL_WEAR_MIN,
                    'TEMPERATURE_DELTA', TEMPERATURE_DELTA,
                    'POWER_PROXY', POWER_PROXY,
                    'WEAR_TORQUE_INTERACTION',
                        WEAR_TORQUE_INTERACTION
                )
            ) AS RNF_PREDICTION

        FROM INPUT_DATA
    )

    SELECT

        FAILURE_PREDICTION:"class"::STRING
            AS FAILURE_CLASS,

        FAILURE_PREDICTION:"probability":"1"::FLOAT
            AS FAILURE_PROBABILITY,

        TWF_PREDICTION:"probability":"1"::FLOAT
            AS TWF_PROBABILITY,

        HDF_PREDICTION:"probability":"1"::FLOAT
            AS HDF_PROBABILITY,

        PWF_PREDICTION:"probability":"1"::FLOAT
            AS PWF_PROBABILITY,

        OSF_PREDICTION:"probability":"1"::FLOAT
            AS OSF_PROBABILITY,

        RNF_PREDICTION:"probability":"1"::FLOAT
            AS RNF_PROBABILITY

    FROM PREDICTIONS
    """

    return session.sql(
        prediction_query
    ).collect()[0]


# ============================================================
# RCA ENGINE
# ============================================================

def generate_rca(
    failure_probability,
    mode_probabilities,
    sensor_values,
    warning_threshold,
    critical_threshold,
):

    ranked_modes = sorted(
        mode_probabilities.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    strongest_mode, strongest_probability = ranked_modes[0]

    temperature_delta = sensor_values["temperature_delta"]
    rpm = sensor_values["rpm"]
    torque_value = sensor_values["torque"]
    wear = sensor_values["wear"]

    # --------------------------------------------------------
    # Overall risk
    # --------------------------------------------------------

    if failure_probability >= critical_threshold:
        status = "CRITICAL"

    elif failure_probability >= warning_threshold:
        status = "WARNING"

    else:
        status = "NORMAL"

    # --------------------------------------------------------
    # Primary diagnostic signal
    # --------------------------------------------------------

    if strongest_probability >= 0.50:

        diagnosis = (
            f"The strongest diagnostic signal is "
            f"**{MODEL_NAMES[strongest_mode]} ({strongest_mode})**, "
            f"with an estimated probability of "
            f"**{strongest_probability * 100:.2f}%**."
        )

        action = MODEL_ACTIONS[strongest_mode]

    elif failure_probability >= critical_threshold:

        diagnosis = (
            "The overall failure model indicates a high risk of "
            "machine failure, but none of the individual "
            "failure-mode models provides a strong dominant "
            "diagnosis."
        )

        action = (
            "Perform a general machine inspection and review the "
            "current operating conditions before continued "
            "operation."
        )

    elif failure_probability >= warning_threshold:

        diagnosis = (
            "The machine is showing an elevated failure signal, "
            "but there is no strongly dominant failure mode."
        )

        action = (
            "Continue monitoring the machine and inspect operating "
            "conditions if the risk continues to increase."
        )

    else:

        diagnosis = (
            "The model does not indicate a strong immediate "
            "machine failure signal under the supplied operating "
            "conditions."
        )

        action = (
            "No immediate maintenance intervention is indicated. "
            "Continue normal monitoring."
        )

    # --------------------------------------------------------
    # Sensor context
    # --------------------------------------------------------

    context = []

    if temperature_delta >= 15:
        context.append(
            f"temperature delta is elevated "
            f"({temperature_delta:.1f} K)"
        )

    if rpm >= 2000:
        context.append(
            f"rotational speed is relatively high "
            f"({rpm:,.0f} RPM)"
        )

    if torque_value >= 60:
        context.append(
            f"torque is relatively high "
            f"({torque_value:.1f} Nm)"
        )

    if wear >= 200:
        context.append(
            f"tool wear is high "
            f"({wear:.0f} min)"
        )

    if context:

        sensor_context = (
            "Relevant operating signals include "
            + ", ".join(context)
            + "."
        )

    else:

        sensor_context = (
            "The supplied operating conditions do not show an "
            "obvious extreme in the monitored sensor values."
        )

    return (
        status,
        diagnosis,
        sensor_context,
        action,
        strongest_mode,
    )


# ============================================================
# EMAIL FUNCTION
# ============================================================
def send_failure_email(
    failure_probability,
    predicted_class,
    mode_probabilities,
    strongest_mode,
    diagnosis,
    action,
    sensor_values,
):
    """
    Send a professionally formatted HTML critical-failure alert.
    """

    subject = (
        f"🚨 MFG Sentinel | Critical Machine Failure | "
        f"{failure_probability * 100:.1f}% Risk"
    )

    # --------------------------------------------------------
    # Rank failure modes
    # --------------------------------------------------------

    ranked_modes = sorted(
        mode_probabilities.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    # --------------------------------------------------------
    # Escape text that will be inserted into HTML
    # --------------------------------------------------------

    safe_diagnosis = html.escape(
        diagnosis.replace("**", "")
    )

    safe_action = html.escape(
        action.replace("**", "")
    )

    # --------------------------------------------------------
    # Severity styling
    # --------------------------------------------------------

    if failure_probability >= 0.90:
        severity = "CRITICAL"
        severity_text = "IMMEDIATE ATTENTION REQUIRED"
        severity_bg = "#b91c1c"
        severity_light = "#fee2e2"
    else:
        severity = "HIGH RISK"
        severity_text = "MAINTENANCE REVIEW RECOMMENDED"
        severity_bg = "#dc2626"
        severity_light = "#fef2f2"

    # --------------------------------------------------------
    # Failure mode rows
    # --------------------------------------------------------

    mode_rows = ""

    for mode, probability in ranked_modes:

        percentage = probability * 100

        if percentage >= 70:
            bar_color = "#dc2626"
        elif percentage >= 30:
            bar_color = "#d97706"
        else:
            bar_color = "#64748b"

        mode_rows += f"""
        <tr>
            <td style="
                padding:12px 10px;
                border-bottom:1px solid #e5e7eb;
                font-weight:600;
                color:#111827;
            ">
                {html.escape(MODE_NAMES.get(mode, mode) if 'MODE_NAMES' in globals() else MODEL_NAMES[mode])}
            </td>

            <td style="
                padding:12px 10px;
                border-bottom:1px solid #e5e7eb;
                color:#475569;
                font-weight:600;
            ">
                {mode}
            </td>

            <td style="
                padding:12px 10px;
                border-bottom:1px solid #e5e7eb;
                text-align:right;
                font-weight:700;
            ">
                {percentage:.4f}%
            </td>

            <td style="
                padding:12px 10px;
                border-bottom:1px solid #e5e7eb;
                width:180px;
            ">
                <div style="
                    width:160px;
                    height:8px;
                    background:#e5e7eb;
                    border-radius:8px;
                ">
                    <div style="
                        width:{min(percentage, 100):.2f}%;
                        height:8px;
                        background:{bar_color};
                        border-radius:8px;
                    "></div>
                </div>
            </td>
        </tr>
        """

    # --------------------------------------------------------
    # Primary diagnostic
    # --------------------------------------------------------

    strongest_probability = mode_probabilities[strongest_mode]

    # --------------------------------------------------------
    # HTML email
    # --------------------------------------------------------

    email_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>MFG Sentinel Alert</title>
</head>

<body style="
    margin:0;
    padding:0;
    background:#f3f4f6;
    font-family:Arial,Helvetica,sans-serif;
    color:#111827;
">

<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:#f3f4f6;padding:30px 0;">

<tr>
<td align="center">

<table width="700" cellpadding="0" cellspacing="0" border="0"
       style="
            width:700px;
            max-width:94%;
            background:#ffffff;
            border-radius:14px;
            overflow:hidden;
            box-shadow:0 3px 14px rgba(0,0,0,0.08);
       ">

<!-- ===================================================== -->
<!-- HEADER -->
<!-- ===================================================== -->

<tr>
<td style="
    background:#111827;
    padding:24px 30px;
">

<table width="100%" cellpadding="0" cellspacing="0">
<tr>

<td>
    <div style="
        font-size:24px;
        font-weight:700;
        color:#ffffff;
    ">
        🏭 MFG Sentinel
    </div>

    <div style="
        margin-top:5px;
        font-size:13px;
        color:#cbd5e1;
    ">
        Predictive Maintenance Command Center
    </div>
</td>

<td align="right">
    <div style="
        display:inline-block;
        background:{severity_bg};
        color:#ffffff;
        padding:8px 12px;
        border-radius:20px;
        font-size:12px;
        font-weight:700;
    ">
        {severity}
    </div>
</td>

</tr>
</table>

</td>
</tr>


<!-- ===================================================== -->
<!-- ALERT BANNER -->
<!-- ===================================================== -->

<tr>
<td style="
    padding:20px 30px;
    background:{severity_light};
    border-bottom:1px solid #fecaca;
">

<div style="
    font-size:20px;
    font-weight:700;
    color:#991b1b;
">
    🚨 Critical Machine Failure Detected
</div>

<div style="
    margin-top:6px;
    font-size:14px;
    color:#7f1d1d;
">
    {severity_text}
</div>

</td>
</tr>


<!-- ===================================================== -->
<!-- RISK KPI CARDS -->
<!-- ===================================================== -->

<tr>
<td style="padding:25px 30px 10px 30px;">

<table width="100%" cellpadding="0" cellspacing="0">

<tr>

<td width="32%" style="padding-right:8px;">
<div style="
    background:#fef2f2;
    border:1px solid #fecaca;
    border-radius:10px;
    padding:16px;
">
    <div style="
        font-size:12px;
        color:#64748b;
        text-transform:uppercase;
        font-weight:600;
    ">
        Failure Probability
    </div>

    <div style="
        margin-top:6px;
        font-size:28px;
        font-weight:700;
        color:#b91c1c;
    ">
        {failure_probability * 100:.2f}%
    </div>
</div>
</td>


<td width="32%" style="padding:0 4px;">
<div style="
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:10px;
    padding:16px;
">
    <div style="
        font-size:12px;
        color:#64748b;
        text-transform:uppercase;
        font-weight:600;
    ">
        Predicted Class
    </div>

    <div style="
        margin-top:6px;
        font-size:28px;
        font-weight:700;
        color:#111827;
    ">
        {html.escape(predicted_class)}
    </div>
</div>
</td>


<td width="32%" style="padding-left:8px;">
<div style="
    background:#fff7ed;
    border:1px solid #fed7aa;
    border-radius:10px;
    padding:16px;
">
    <div style="
        font-size:12px;
        color:#64748b;
        text-transform:uppercase;
        font-weight:600;
    ">
        Primary Signal
    </div>

    <div style="
        margin-top:6px;
        font-size:18px;
        font-weight:700;
        color:#9a3412;
    ">
        {html.escape(MODEL_NAMES[strongest_mode])}
    </div>

    <div style="
        margin-top:4px;
        font-size:13px;
        color:#7c2d12;
    ">
        {strongest_probability * 100:.2f}% probability
    </div>
</div>
</td>

</tr>

</table>

</td>
</tr>


<!-- ===================================================== -->
<!-- SENSOR CONDITIONS -->
<!-- ===================================================== -->

<tr>
<td style="padding:10px 30px 5px 30px;">

<div style="
    font-size:17px;
    font-weight:700;
    color:#111827;
    margin-bottom:12px;
">
    📡 Machine Conditions
</div>

<table width="100%" cellpadding="0" cellspacing="0"
       style="
            border-collapse:collapse;
            border:1px solid #e5e7eb;
            border-radius:8px;
       ">

<tr style="background:#f8fafc;">
    <th align="left" style="padding:11px;color:#64748b;font-size:12px;">
        SENSOR
    </th>
    <th align="right" style="padding:11px;color:#64748b;font-size:12px;">
        VALUE
    </th>
</tr>

<tr>
    <td style="padding:11px;border-top:1px solid #e5e7eb;">
        Air Temperature
    </td>
    <td align="right" style="padding:11px;border-top:1px solid #e5e7eb;font-weight:600;">
        {sensor_values["air_temperature"]:.2f} K
    </td>
</tr>

<tr>
    <td style="padding:11px;border-top:1px solid #e5e7eb;">
        Process Temperature
    </td>
    <td align="right" style="padding:11px;border-top:1px solid #e5e7eb;font-weight:600;">
        {sensor_values["process_temperature"]:.2f} K
    </td>
</tr>

<tr>
    <td style="padding:11px;border-top:1px solid #e5e7eb;">
        Rotational Speed
    </td>
    <td align="right" style="padding:11px;border-top:1px solid #e5e7eb;font-weight:600;">
        {sensor_values["rpm"]:.0f} RPM
    </td>
</tr>

<tr>
    <td style="padding:11px;border-top:1px solid #e5e7eb;">
        Torque
    </td>
    <td align="right" style="padding:11px;border-top:1px solid #e5e7eb;font-weight:600;">
        {sensor_values["torque"]:.2f} Nm
    </td>
</tr>

<tr>
    <td style="padding:11px;border-top:1px solid #e5e7eb;">
        Tool Wear
    </td>
    <td align="right" style="padding:11px;border-top:1px solid #e5e7eb;font-weight:600;">
        {sensor_values["wear"]:.0f} min
    </td>
</tr>

</table>

</td>
</tr>


<!-- ===================================================== -->
<!-- FAILURE MODES -->
<!-- ===================================================== -->

<tr>
<td style="padding:25px 30px 10px 30px;">

<div style="
    font-size:17px;
    font-weight:700;
    color:#111827;
    margin-bottom:12px;
">
    🔬 Failure Mode Diagnostics
</div>

<table width="100%" cellpadding="0" cellspacing="0"
       style="border-collapse:collapse;">

<tr style="background:#f8fafc;">
    <th align="left" style="padding:10px;font-size:12px;color:#64748b;">
        FAILURE MODE
    </th>
    <th align="left" style="padding:10px;font-size:12px;color:#64748b;">
        CODE
    </th>
    <th align="right" style="padding:10px;font-size:12px;color:#64748b;">
        PROBABILITY
    </th>
    <th style="padding:10px;font-size:12px;color:#64748b;">
        SIGNAL
    </th>
</tr>

{mode_rows}

</table>

</td>
</tr>


<!-- ===================================================== -->
<!-- RCA -->
<!-- ===================================================== -->

<tr>
<td style="padding:20px 30px;">

<div style="
    background:#f8fafc;
    border-left:5px solid #475569;
    padding:18px;
    border-radius:8px;
">

<div style="
    font-size:17px;
    font-weight:700;
    color:#111827;
    margin-bottom:10px;
">
    🧠 Root Cause Analysis
</div>

<div style="
    font-size:14px;
    line-height:1.7;
    color:#334155;
">
    {safe_diagnosis}
</div>

</div>

</td>
</tr>


<!-- ===================================================== -->
<!-- RECOMMENDED ACTION -->
<!-- ===================================================== -->

<tr>
<td style="padding:5px 30px 25px 30px;">

<div style="
    background:#eff6ff;
    border:1px solid #bfdbfe;
    border-radius:10px;
    padding:18px;
">

<div style="
    font-size:17px;
    font-weight:700;
    color:#1e3a8a;
    margin-bottom:8px;
">
    🛠️ Recommended Action
</div>

<div style="
    font-size:14px;
    line-height:1.7;
    color:#1e40af;
">
    {safe_action}
</div>

</div>

</td>
</tr>


<!-- ===================================================== -->
<!-- DERIVED FEATURES -->
<!-- ===================================================== -->

<tr>
<td style="padding:0 30px 25px 30px;">

<div style="
    font-size:15px;
    font-weight:700;
    color:#334155;
    margin-bottom:10px;
">
    📐 Derived Signals
</div>

<table width="100%" cellpadding="0" cellspacing="0">
<tr>

<td style="
    background:#f8fafc;
    border:1px solid #e2e8f0;
    padding:12px;
    border-radius:8px;
">
    <div style="font-size:11px;color:#64748b;">
        TEMPERATURE DELTA
    </div>
    <div style="font-size:16px;font-weight:700;margin-top:4px;">
        {sensor_values["temperature_delta"]:.2f} K
    </div>
</td>

<td width="12"></td>

<td style="
    background:#f8fafc;
    border:1px solid #e2e8f0;
    padding:12px;
    border-radius:8px;
">
    <div style="font-size:11px;color:#64748b;">
        POWER PROXY
    </div>
    <div style="font-size:16px;font-weight:700;margin-top:4px;">
        {sensor_values["power_proxy"]:,.0f}
    </div>
</td>

<td width="12"></td>

<td style="
    background:#f8fafc;
    border:1px solid #e2e8f0;
    padding:12px;
    border-radius:8px;
">
    <div style="font-size:11px;color:#64748b;">
        WEAR × TORQUE
    </div>
    <div style="font-size:16px;font-weight:700;margin-top:4px;">
        {sensor_values["wear_torque_interaction"]:,.0f}
    </div>
</td>

</tr>
</table>

</td>
</tr>


<!-- ===================================================== -->
<!-- FOOTER -->
<!-- ===================================================== -->

<tr>
<td style="
    background:#111827;
    padding:20px 30px;
">

<div style="
    color:#e2e8f0;
    font-size:12px;
    line-height:1.6;
">
    <b>MFG Sentinel</b><br>
    Automated predictive-maintenance alert generated from
    Snowflake ML inference.
</div>

<div style="
    margin-top:10px;
    color:#94a3b8;
    font-size:11px;
    line-height:1.5;
">
    RNF is treated as a low-confidence diagnostic signal because
    it is extremely rare in the underlying AI4I dataset.
    This alert is intended to support maintenance decisions and
    should be validated against operational conditions.
</div>

</td>
</tr>

</table>

</td>
</tr>

</table>

</body>
</html>
"""

    # --------------------------------------------------------
    # Escape SQL single quotes
    # --------------------------------------------------------

    safe_subject = subject.replace("'", "''")
    safe_html = email_html.replace("'", "''")
    safe_recipient = EMAIL_RECIPIENT.replace("'", "''")

    # --------------------------------------------------------
    # Send HTML email
    # --------------------------------------------------------

    email_query = f"""
    CALL SYSTEM$SEND_EMAIL(
        '{EMAIL_INTEGRATION}',
        '{safe_recipient}',
        '{safe_subject}',
        '{safe_html}',
        'text/html'
    )
    """

    result = session.sql(email_query).collect()[0]

    return result






# ============================================================
# ANALYZE BUTTON
# ============================================================

st.divider()

analyze = st.button(
    "🔍 Analyze Machine",
    type="primary",
    use_container_width=True,
)

if analyze:

    with st.spinner(
        "Running six predictive-maintenance models..."
    ):

        try:

            # ------------------------------------------------
            # Run models
            # ------------------------------------------------

            result = run_all_models(
                air_temperature,
                process_temperature,
                rotational_speed,
                torque,
                tool_wear,
                temperature_delta,
                power_proxy,
                wear_torque_interaction,
            )

            # ------------------------------------------------
            # Extract probabilities
            # ------------------------------------------------

            failure_probability = float(
                result["FAILURE_PROBABILITY"]
            )

            twf_probability = float(
                result["TWF_PROBABILITY"]
            )

            hdf_probability = float(
                result["HDF_PROBABILITY"]
            )

            pwf_probability = float(
                result["PWF_PROBABILITY"]
            )

            osf_probability = float(
                result["OSF_PROBABILITY"]
            )

            rnf_probability = float(
                result["RNF_PROBABILITY"]
            )

            predicted_class = str(
                result["FAILURE_CLASS"]
            )

            # ------------------------------------------------
            # Failure mode dictionary
            # ------------------------------------------------

            mode_probabilities = {
                "TWF": twf_probability,
                "HDF": hdf_probability,
                "PWF": pwf_probability,
                "OSF": osf_probability,
                "RNF": rnf_probability,
            }

            # ------------------------------------------------
            # Sensor values
            # ------------------------------------------------

            sensor_values = {
                "air_temperature": air_temperature,
                "process_temperature": process_temperature,
                "rpm": rotational_speed,
                "torque": torque,
                "wear": tool_wear,
                "temperature_delta": temperature_delta,
                "power_proxy": power_proxy,
                "wear_torque_interaction":
                    wear_torque_interaction,
            }

            # ------------------------------------------------
            # RCA
            # ------------------------------------------------

            (
                status,
                diagnosis,
                sensor_context,
                action,
                strongest_mode,
            ) = generate_rca(
                failure_probability=failure_probability,
                mode_probabilities=mode_probabilities,
                sensor_values=sensor_values,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
            )

            # =================================================
            # OVERALL MACHINE RISK
            # =================================================

            st.markdown(
                '<div class="section-title">'
                "🚨 Overall Machine Risk"
                "</div>",
                unsafe_allow_html=True,
            )

            r1, r2, r3 = st.columns(3)

            with r1:

                st.metric(
                    "Failure Probability",
                    f"{failure_probability * 100:.2f}%",
                )

            with r2:

                st.metric(
                    "Risk Level",
                    status,
                )

            with r3:

                st.metric(
                    "Predicted Class",
                    predicted_class,
                )

            st.progress(
                min(
                    max(failure_probability, 0.0),
                    1.0,
                ),
                text=(
                    f"Failure Risk: "
                    f"{failure_probability * 100:.2f}%"
                ),
            )

            if status == "CRITICAL":

                st.error(
                    "🔴 CRITICAL: The model indicates a high "
                    "probability of machine failure."
                )

            elif status == "WARNING":

                st.warning(
                    "🟡 WARNING: The machine is showing an "
                    "elevated failure signal."
                )

            else:

                st.success(
                    "🟢 NORMAL: No strong immediate failure "
                    "signal was detected."
                )

            # =================================================
            # FAILURE MODE DIAGNOSTICS
            # =================================================

            st.markdown(
                '<div class="section-title">'
                "🔬 Failure Mode Diagnostics"
                "</div>",
                unsafe_allow_html=True,
            )

            diagnostic_cols = st.columns(5)

            for column, (mode, probability) in zip(
                diagnostic_cols,
                mode_probabilities.items(),
            ):

                with column:

                    st.metric(
                        mode,
                        f"{probability * 100:.2f}%",
                    )

                    st.caption(
                        MODEL_NAMES[mode]
                    )

                    st.progress(
                        min(
                            max(probability, 0.0),
                            1.0,
                        )
                    )

            # =================================================
            # RANKED DIAGNOSTIC SIGNALS
            # =================================================

            st.markdown(
                '<div class="section-title">'
                "📊 Ranked Diagnostic Signals"
                "</div>",
                unsafe_allow_html=True,
            )

            ranked_modes = sorted(
                mode_probabilities.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            for rank, (mode, probability) in enumerate(
                ranked_modes,
                start=1,
            ):

                st.write(
                    f"**{rank}. {MODEL_NAMES[mode]} ({mode})** — "
                    f"{probability * 100:.4f}%"
                )

            # =================================================
            # ROOT CAUSE ANALYSIS
            # =================================================

            st.markdown(
                '<div class="section-title">'
                "🧠 Root Cause Analysis"
                "</div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="rca-box">

                <b>Primary Diagnostic Signal</b><br>
                {MODEL_NAMES[strongest_mode]}
                ({strongest_mode}) —
                {mode_probabilities[strongest_mode] * 100:.2f}%

                <br><br>

                <b>Diagnosis</b><br>
                {diagnosis}

                <br><br>

                <b>Sensor Context</b><br>
                {sensor_context}

                </div>
                """,
                unsafe_allow_html=True,
            )

            # =================================================
            # RECOMMENDED ACTION
            # =================================================

            st.markdown(
                '<div class="section-title">'
                "🛠️ Recommended Action"
                "</div>",
                unsafe_allow_html=True,
            )

            if status == "CRITICAL":

                st.error(action)

            elif status == "WARNING":

                st.warning(action)

            else:

                st.info(action)

            # =================================================
            # INPUT SUMMARY
            # =================================================

            with st.expander("📋 View Machine Inputs"):

                input_rows = {
                    "Air Temperature (K)": air_temperature,
                    "Process Temperature (K)": process_temperature,
                    "Rotational Speed (RPM)": rotational_speed,
                    "Torque (Nm)": torque,
                    "Tool Wear (min)": tool_wear,
                    "Temperature Delta": temperature_delta,
                    "Power Proxy": power_proxy,
                    "Wear × Torque":
                        wear_torque_interaction,
                }

                st.dataframe(
                    input_rows,
                    use_container_width=True,
                )

            # =================================================
            # MODEL OUTPUTS
            # =================================================

            with st.expander("🔎 View Model Outputs"):

                st.write(
                    {
                        "overall_failure_model": {
                            "predicted_class":
                                predicted_class,
                            "failure_probability":
                                failure_probability,
                        },
                        "failure_modes":
                            mode_probabilities,
                    }
                )

            # =================================================
            # RNF CAVEAT
            # =================================================

            st.caption(
                "RNF is extremely rare in the AI4I dataset and "
                "its model has weak predictive discrimination. "
                "It is therefore treated as a low-confidence "
                "diagnostic signal rather than a primary "
                "root cause."
            )

            # =================================================
            # ALERT + EMAIL
            # =================================================

            st.markdown(
                '<div class="section-title">'
                "📡 Alert Status"
                "</div>",
                unsafe_allow_html=True,
            )

            if failure_probability >= critical_threshold:

                st.error(
                    "🚨 Critical failure threshold exceeded."
                )

                # ------------------------------------------------
                # SEND EMAIL
                # ------------------------------------------------

                with st.spinner(
                    "Sending critical machine alert..."
                ):

                    try:

                        email_result = send_failure_email(
                            failure_probability=
                                failure_probability,
                            predicted_class=
                                predicted_class,
                            mode_probabilities=
                                mode_probabilities,
                            strongest_mode=
                                strongest_mode,
                            diagnosis=
                                diagnosis,
                            action=
                                action,
                            sensor_values=
                                sensor_values,
                        )

                        st.success(
                            "📧 Critical failure alert sent "
                            f"to {EMAIL_RECIPIENT}."
                        )

                        with st.expander(
                            "View email trigger result"
                        ):

                            st.write(email_result)

                    except Exception as email_error:

                        st.error(
                            "The machine was classified as "
                            "critical, but the email alert "
                            "could not be sent."
                        )

                        st.exception(email_error)

            elif failure_probability >= warning_threshold:

                st.warning(
                    "⚠️ Warning threshold exceeded. "
                    "Continue monitoring the machine."
                )

            else:

                st.success(
                    "✅ No alert required."
                )

        except Exception as e:

            st.error(
                "An error occurred while running the "
                "Snowflake ML models."
            )

            st.exception(e)

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MFG Sentinel | Snowflake Predictive Maintenance "
    "Command Center"
)

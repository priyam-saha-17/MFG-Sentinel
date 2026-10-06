
import streamlit as st
import os
import html
import uuid
from datetime import datetime

st.set_page_config(
    page_title="MFG Sentinel",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

conn = st.connection(
    "snowflake",
    ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"),
)
session = conn.session()

DATABASE = "MFG_SENTINEL"
SCHEMA = "ANALYTICS"
EVENTS_TABLE = f"{DATABASE}.{SCHEMA}.MACHINE_ANALYSIS_EVENTS"
INCIDENTS_TABLE = f"{DATABASE}.{SCHEMA}.INCIDENT_REGISTER"

EMAIL_INTEGRATION = "MFG_SENTINEL_EMAIL_INT"
EMAIL_RECIPIENT = "impriyamsaha@gmail.com"

DEFAULT_WARNING_THRESHOLD = 0.30
DEFAULT_CRITICAL_THRESHOLD = 0.70

MODEL_NAMES = {
    "TWF": "Tool Wear Failure",
    "HDF": "Heat Dissipation Failure",
    "PWF": "Power Failure",
    "OSF": "Overstrain Failure",
    "RNF": "Random Failure",
}

MODEL_ACTIONS = {
    "TWF": "Inspect tool condition and consider tool replacement or maintenance before continued operation.",
    "HDF": "Inspect cooling and thermal conditions. Check whether the machine is operating under excessive thermal load.",
    "PWF": "Inspect motor/load conditions, power delivery, and operating parameters for excessive power demand.",
    "OSF": "Inspect mechanical loading and process stress. Consider reducing load or checking for excessive torque.",
    "RNF": "A random-failure signal was detected. Because RNF is extremely rare in the available dataset, treat this as a low-confidence diagnostic signal and perform a general inspection.",
}


def sql_escape(value):
    return str(value).replace("'", "''")


def generate_event_id():
    return f"EVT-{uuid.uuid4().hex[:12].upper()}"


def generate_incident_id():
    return f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def check_app_tables():
    """Verify that the native persistence tables already exist.

    The application does not create tables at runtime so a public/restricted
    service role only needs SELECT/INSERT/UPDATE privileges on these tables.
    """
    session.sql(f"SELECT 1 FROM {EVENTS_TABLE} LIMIT 1").collect()
    session.sql(f"SELECT 1 FROM {INCIDENTS_TABLE} LIMIT 1").collect()


try:
    check_app_tables()
    persistence_ready = True
except Exception as setup_error:
    persistence_ready = False
    st.error(
        "The MFG Sentinel persistence tables are not available. "
        "Run MFG_Sentinel_App_Setup.sql once in Snowflake, then rerun the app."
    )
    with st.expander("Database setup error"):
        st.exception(setup_error)


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
    query = f"""
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
                    'WEAR_TORQUE_INTERACTION', WEAR_TORQUE_INTERACTION
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
                    'WEAR_TORQUE_INTERACTION', WEAR_TORQUE_INTERACTION
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
                    'WEAR_TORQUE_INTERACTION', WEAR_TORQUE_INTERACTION
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
                    'WEAR_TORQUE_INTERACTION', WEAR_TORQUE_INTERACTION
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
                    'WEAR_TORQUE_INTERACTION', WEAR_TORQUE_INTERACTION
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
                    'WEAR_TORQUE_INTERACTION', WEAR_TORQUE_INTERACTION
                )
            ) AS RNF_PREDICTION
        FROM INPUT_DATA
    )
    SELECT
        FAILURE_PREDICTION:"class"::STRING AS FAILURE_CLASS,
        FAILURE_PREDICTION:"probability":"1"::FLOAT AS FAILURE_PROBABILITY,
        TWF_PREDICTION:"probability":"1"::FLOAT AS TWF_PROBABILITY,
        HDF_PREDICTION:"probability":"1"::FLOAT AS HDF_PROBABILITY,
        PWF_PREDICTION:"probability":"1"::FLOAT AS PWF_PROBABILITY,
        OSF_PREDICTION:"probability":"1"::FLOAT AS OSF_PROBABILITY,
        RNF_PREDICTION:"probability":"1"::FLOAT AS RNF_PROBABILITY
    FROM PREDICTIONS
    """
    return session.sql(query).collect()[0]


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

    if failure_probability >= critical_threshold:
        status = "CRITICAL"
    elif failure_probability >= warning_threshold:
        status = "WARNING"
    else:
        status = "NORMAL"

    if strongest_probability >= 0.50:
        diagnosis = (
            f"The strongest diagnostic signal is {MODEL_NAMES[strongest_mode]} "
            f"({strongest_mode}), with an estimated probability of "
            f"{strongest_probability * 100:.2f}%."
        )
        action = MODEL_ACTIONS[strongest_mode]
    elif failure_probability >= critical_threshold:
        diagnosis = (
            "The overall failure model indicates a high risk of machine "
            "failure, but none of the individual failure-mode models provides "
            "a strong dominant diagnosis."
        )
        action = (
            "Perform a general machine inspection and review the current "
            "operating conditions before continued operation."
        )
    elif failure_probability >= warning_threshold:
        diagnosis = (
            "The machine is showing an elevated failure signal, but there "
            "is no strongly dominant failure mode."
        )
        action = (
            "Continue monitoring the machine and inspect operating conditions "
            "if the risk continues to increase."
        )
    else:
        diagnosis = (
            "The model does not indicate a strong immediate machine failure "
            "signal under the supplied operating conditions."
        )
        action = (
            "No immediate maintenance intervention is indicated. "
            "Continue normal monitoring."
        )

    context = []
    if temperature_delta >= 15:
        context.append(f"temperature delta is elevated ({temperature_delta:.1f} K)")
    if rpm >= 2000:
        context.append(f"rotational speed is relatively high ({rpm:,.0f} RPM)")
    if torque_value >= 60:
        context.append(f"torque is relatively high ({torque_value:.1f} Nm)")
    if wear >= 200:
        context.append(f"tool wear is high ({wear:.0f} min)")

    sensor_context = (
        "Relevant operating signals include " + ", ".join(context) + "."
        if context
        else
        "The supplied operating conditions do not show an obvious extreme "
        "in the monitored sensor values."
    )

    return status, diagnosis, sensor_context, action, strongest_mode


def save_analysis_event(
    event_id,
    failure_class,
    failure_probability,
    mode_probabilities,
    status,
    strongest_mode,
    diagnosis,
    sensor_context,
    action,
    sensor_values,
):
    query = f"""
    INSERT INTO {EVENTS_TABLE} (
        EVENT_ID, EVENT_TS, SOURCE,
        AIR_TEMPERATURE_K, PROCESS_TEMPERATURE_K,
        ROTATIONAL_SPEED_RPM, TORQUE_NM, TOOL_WEAR_MIN,
        TEMPERATURE_DELTA, POWER_PROXY, WEAR_TORQUE_INTERACTION,
        FAILURE_CLASS, FAILURE_PROBABILITY,
        TWF_PROBABILITY, HDF_PROBABILITY, PWF_PROBABILITY,
        OSF_PROBABILITY, RNF_PROBABILITY,
        RISK_LEVEL, PRIMARY_FAILURE_MODE,
        DIAGNOSIS, SENSOR_CONTEXT, RECOMMENDED_ACTION
    )
    VALUES (
        '{sql_escape(event_id)}', CURRENT_TIMESTAMP(), 'STREAMLIT_INPUT',
        {sensor_values["air_temperature"]},
        {sensor_values["process_temperature"]},
        {sensor_values["rpm"]},
        {sensor_values["torque"]},
        {sensor_values["wear"]},
        {sensor_values["temperature_delta"]},
        {sensor_values["power_proxy"]},
        {sensor_values["wear_torque_interaction"]},
        '{sql_escape(failure_class)}',
        {failure_probability},
        {mode_probabilities["TWF"]},
        {mode_probabilities["HDF"]},
        {mode_probabilities["PWF"]},
        {mode_probabilities["OSF"]},
        {mode_probabilities["RNF"]},
        '{sql_escape(status)}',
        '{sql_escape(strongest_mode)}',
        '{sql_escape(diagnosis)}',
        '{sql_escape(sensor_context)}',
        '{sql_escape(action)}'
    )
    """
    session.sql(query).collect()


def create_incident(
    event_id,
    severity,
    failure_probability,
    failure_class,
    primary_failure_mode,
    diagnosis,
    sensor_context,
    action,
):
    incident_id = generate_incident_id()

    query = f"""
    INSERT INTO {INCIDENTS_TABLE} (
        INCIDENT_ID, EVENT_ID, CREATED_AT, UPDATED_AT,
        SEVERITY, STATUS, FAILURE_PROBABILITY, FAILURE_CLASS,
        PRIMARY_FAILURE_MODE, DIAGNOSIS, SENSOR_CONTEXT,
        RECOMMENDED_ACTION, EMAIL_SENT
    )
    VALUES (
        '{sql_escape(incident_id)}',
        '{sql_escape(event_id)}',
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(),
        '{sql_escape(severity)}',
        'OPEN',
        {failure_probability},
        '{sql_escape(failure_class)}',
        '{sql_escape(primary_failure_mode)}',
        '{sql_escape(diagnosis)}',
        '{sql_escape(sensor_context)}',
        '{sql_escape(action)}',
        FALSE
    )
    """
    session.sql(query).collect()
    return incident_id


def send_failure_email(
    failure_probability,
    predicted_class,
    mode_probabilities,
    strongest_mode,
    diagnosis,
    action,
    sensor_values,
    incident_id,
):
    subject = (
        f"MFG Sentinel | {incident_id} | Critical Machine Failure | "
        f"{failure_probability * 100:.1f}% Risk"
    )

    safe_diagnosis = html.escape(diagnosis)
    safe_action = html.escape(action)

    ranked_modes = sorted(
        mode_probabilities.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    mode_rows = ""
    for mode, probability in ranked_modes:
        percentage = probability * 100
        bar_color = (
            "#dc2626" if percentage >= 70
            else "#d97706" if percentage >= 30
            else "#64748b"
        )
        mode_rows += f"""
        <tr>
            <td style="padding:12px 10px;border-bottom:1px solid #e5e7eb;font-weight:600;color:#111827;">
                {html.escape(MODEL_NAMES[mode])}
            </td>
            <td style="padding:12px 10px;border-bottom:1px solid #e5e7eb;color:#475569;font-weight:600;">
                {mode}
            </td>
            <td style="padding:12px 10px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:700;">
                {percentage:.4f}%
            </td>
            <td style="padding:12px 10px;border-bottom:1px solid #e5e7eb;">
                <div style="width:160px;height:8px;background:#e5e7eb;border-radius:8px;">
                    <div style="width:{min(percentage,100):.2f}%;height:8px;background:{bar_color};border-radius:8px;"></div>
                </div>
            </td>
        </tr>
        """

    email_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#111827;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:30px 0;">
        <tr><td align="center">
          <table width="700" cellpadding="0" cellspacing="0"
                 style="width:700px;max-width:94%;background:#fff;border-radius:14px;overflow:hidden;">
            <tr>
              <td style="background:#111827;padding:24px 30px;">
                <div style="font-size:24px;font-weight:700;color:#fff;">🏭 MFG Sentinel</div>
                <div style="margin-top:5px;font-size:13px;color:#cbd5e1;">Predictive Maintenance Command Center</div>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 30px;background:#fee2e2;border-bottom:1px solid #fecaca;">
                <div style="font-size:20px;font-weight:700;color:#991b1b;">🚨 Critical Machine Failure Detected</div>
                <div style="margin-top:6px;font-size:13px;color:#7f1d1d;">Incident {html.escape(incident_id)}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:25px 30px 10px 30px;">
                <table width="100%" cellpadding="0" cellspacing="0"><tr>
                  <td width="48%" style="padding-right:8px;">
                    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:16px;">
                      <div style="font-size:12px;color:#64748b;">FAILURE PROBABILITY</div>
                      <div style="font-size:28px;font-weight:700;color:#b91c1c;margin-top:6px;">{failure_probability*100:.2f}%</div>
                    </div>
                  </td>
                  <td width="52%" style="padding-left:8px;">
                    <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:16px;">
                      <div style="font-size:12px;color:#64748b;">PRIMARY DIAGNOSTIC SIGNAL</div>
                      <div style="font-size:18px;font-weight:700;color:#9a3412;margin-top:6px;">{html.escape(MODEL_NAMES[strongest_mode])}</div>
                      <div style="font-size:13px;color:#7c2d12;margin-top:4px;">{mode_probabilities[strongest_mode]*100:.2f}% probability</div>
                    </div>
                  </td>
                </tr></table>
              </td>
            </tr>
            <tr><td style="padding:10px 30px;">
              <div style="font-size:17px;font-weight:700;margin-bottom:12px;">📡 Machine Conditions</div>
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #e5e7eb;">
                <tr style="background:#f8fafc;">
                  <th align="left" style="padding:10px;font-size:12px;color:#64748b;">SENSOR</th>
                  <th align="right" style="padding:10px;font-size:12px;color:#64748b;">VALUE</th>
                </tr>
                <tr><td style="padding:10px;border-top:1px solid #e5e7eb;">Air Temperature</td><td align="right" style="padding:10px;border-top:1px solid #e5e7eb;font-weight:600;">{sensor_values["air_temperature"]:.2f} K</td></tr>
                <tr><td style="padding:10px;border-top:1px solid #e5e7eb;">Process Temperature</td><td align="right" style="padding:10px;border-top:1px solid #e5e7eb;font-weight:600;">{sensor_values["process_temperature"]:.2f} K</td></tr>
                <tr><td style="padding:10px;border-top:1px solid #e5e7eb;">Rotational Speed</td><td align="right" style="padding:10px;border-top:1px solid #e5e7eb;font-weight:600;">{sensor_values["rpm"]:.0f} RPM</td></tr>
                <tr><td style="padding:10px;border-top:1px solid #e5e7eb;">Torque</td><td align="right" style="padding:10px;border-top:1px solid #e5e7eb;font-weight:600;">{sensor_values["torque"]:.2f} Nm</td></tr>
                <tr><td style="padding:10px;border-top:1px solid #e5e7eb;">Tool Wear</td><td align="right" style="padding:10px;border-top:1px solid #e5e7eb;font-weight:600;">{sensor_values["wear"]:.0f} min</td></tr>
              </table>
            </td></tr>
            <tr><td style="padding:25px 30px 10px 30px;">
              <div style="font-size:17px;font-weight:700;margin-bottom:12px;">🔬 Failure Mode Diagnostics</div>
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#f8fafc;">
                  <th align="left" style="padding:10px;font-size:12px;color:#64748b;">FAILURE MODE</th>
                  <th align="left" style="padding:10px;font-size:12px;color:#64748b;">CODE</th>
                  <th align="right" style="padding:10px;font-size:12px;color:#64748b;">PROBABILITY</th>
                  <th style="padding:10px;font-size:12px;color:#64748b;">SIGNAL</th>
                </tr>
                {mode_rows}
              </table>
            </td></tr>
            <tr><td style="padding:20px 30px;">
              <div style="background:#f8fafc;border-left:5px solid #475569;padding:18px;border-radius:8px;">
                <div style="font-size:17px;font-weight:700;margin-bottom:10px;">🧠 Diagnostic Assessment</div>
                <div style="font-size:14px;line-height:1.7;color:#334155;">{safe_diagnosis}</div>
              </div>
            </td></tr>
            <tr><td style="padding:5px 30px 25px 30px;">
              <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:18px;">
                <div style="font-size:17px;font-weight:700;color:#1e3a8a;margin-bottom:8px;">🛠️ Recommended Action</div>
                <div style="font-size:14px;line-height:1.7;color:#1e40af;">{safe_action}</div>
              </div>
            </td></tr>
            <tr><td style="background:#111827;padding:20px 30px;">
              <div style="color:#e2e8f0;font-size:12px;line-height:1.6;">
                <b>MFG Sentinel</b><br>
                Automated predictive-maintenance alert generated from Snowflake ML inference.
              </div>
              <div style="margin-top:10px;color:#94a3b8;font-size:11px;line-height:1.5;">
                RNF is treated as a low-confidence signal because it is extremely rare in the underlying AI4I dataset.
              </div>
            </td></tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    query = f"""
    CALL SYSTEM$SEND_EMAIL(
        '{EMAIL_INTEGRATION}',
        '{sql_escape(EMAIL_RECIPIENT)}',
        '{sql_escape(subject)}',
        '{sql_escape(email_html)}',
        'text/html'
    )
    """
    return session.sql(query).collect()[0]


def mark_email_sent(incident_id):
    session.sql(
        f"""
        UPDATE {INCIDENTS_TABLE}
        SET EMAIL_SENT = TRUE, UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE INCIDENT_ID = '{sql_escape(incident_id)}'
        """
    ).collect()


def get_historical_kpis():
    return session.sql(
        f"""
        SELECT
            COUNT(*) AS TOTAL_OBSERVATIONS,
            SUM(MACHINE_FAILURE) AS OBSERVED_FAILURES,
            ROUND(AVG(MACHINE_FAILURE) * 100, 2) AS FAILURE_RATE_PCT,
            ROUND(AVG(TOOL_WEAR_MIN), 2) AS AVG_TOOL_WEAR_MIN,
            ROUND(AVG(ROTATIONAL_SPEED_RPM), 2) AS AVG_RPM,
            ROUND(AVG(TORQUE_NM), 2) AS AVG_TORQUE_NM,
            ROUND(AVG(TEMPERATURE_DELTA), 2) AS AVG_TEMP_DELTA
        FROM {DATABASE}.ANALYTICS.MACHINE_FEATURES
        """
    ).collect()[0]


def get_live_kpis():
    return session.sql(
        f"""
        SELECT
            COUNT(*) AS ANALYZED_EVENTS,
            COALESCE(SUM(CASE WHEN RISK_LEVEL = 'CRITICAL' THEN 1 ELSE 0 END), 0) AS CRITICAL_EVENTS,
            COALESCE(SUM(CASE WHEN RISK_LEVEL = 'WARNING' THEN 1 ELSE 0 END), 0) AS WARNING_EVENTS,
            ROUND(COALESCE(AVG(FAILURE_PROBABILITY), 0) * 100, 2) AS AVG_LIVE_RISK_PCT,
            MAX(EVENT_TS) AS LAST_ANALYSIS_TS
        FROM {EVENTS_TABLE}
        """
    ).collect()[0]


def get_combined_sensor_kpis():
    return session.sql(
        f"""
        SELECT
            ROUND(AVG(TOOL_WEAR_MIN), 2) AS AVG_COMBINED_TOOL_WEAR_MIN,
            ROUND(AVG(ROTATIONAL_SPEED_RPM), 2) AS AVG_COMBINED_RPM,
            ROUND(AVG(TORQUE_NM), 2) AS AVG_COMBINED_TORQUE_NM,
            ROUND(AVG(TEMPERATURE_DELTA), 2) AS AVG_COMBINED_TEMP_DELTA
        FROM (
            SELECT TOOL_WEAR_MIN, ROTATIONAL_SPEED_RPM, TORQUE_NM, TEMPERATURE_DELTA
            FROM {DATABASE}.ANALYTICS.MACHINE_FEATURES
            UNION ALL
            SELECT TOOL_WEAR_MIN, ROTATIONAL_SPEED_RPM, TORQUE_NM, TEMPERATURE_DELTA
            FROM {EVENTS_TABLE}
        )
        """
    ).collect()[0]


def get_failure_mode_kpis():
    return session.sql(
        f"""
        SELECT
            SUM(TWF) AS TWF_COUNT,
            SUM(HDF) AS HDF_COUNT,
            SUM(PWF) AS PWF_COUNT,
            SUM(OSF) AS OSF_COUNT,
            SUM(RNF) AS RNF_COUNT
        FROM {DATABASE}.ANALYTICS.MACHINE_FEATURES
        """
    ).collect()[0]


def get_recent_events(limit=20):
    return session.sql(
        f"""
        SELECT
            EVENT_TS,
            EVENT_ID,
            RISK_LEVEL,
            ROUND(FAILURE_PROBABILITY * 100, 2) AS FAILURE_RISK_PCT,
            PRIMARY_FAILURE_MODE,
            ROUND(TWF_PROBABILITY * 100, 2) AS TWF_PCT,
            ROUND(HDF_PROBABILITY * 100, 2) AS HDF_PCT,
            ROUND(PWF_PROBABILITY * 100, 2) AS PWF_PCT,
            ROUND(OSF_PROBABILITY * 100, 2) AS OSF_PCT,
            ROUND(RNF_PROBABILITY * 100, 2) AS RNF_PCT,
            ROUND(TOOL_WEAR_MIN, 1) AS TOOL_WEAR_MIN,
            ROUND(ROTATIONAL_SPEED_RPM, 0) AS RPM,
            ROUND(TORQUE_NM, 1) AS TORQUE_NM
        FROM {EVENTS_TABLE}
        ORDER BY EVENT_TS DESC
        LIMIT {int(limit)}
        """
    ).to_pandas()


def get_risk_history():
    return session.sql(
        f"""
        SELECT EVENT_TS, FAILURE_PROBABILITY * 100 AS FAILURE_RISK_PCT
        FROM {EVENTS_TABLE}
        ORDER BY EVENT_TS
        """
    ).to_pandas()


def get_incidents(status_filter="ALL"):
    where_clause = ""
    if status_filter != "ALL":
        where_clause = f"WHERE STATUS = '{sql_escape(status_filter)}'"

    return session.sql(
        f"""
        SELECT
            INCIDENT_ID,
            EVENT_ID,
            CREATED_AT,
            SEVERITY,
            STATUS,
            ROUND(FAILURE_PROBABILITY * 100, 2) AS FAILURE_RISK_PCT,
            PRIMARY_FAILURE_MODE,
            EMAIL_SENT,
            RECOMMENDED_ACTION,
            RESOLUTION_NOTES,
            RESOLVED_AT
        FROM {INCIDENTS_TABLE}
        {where_clause}
        ORDER BY CREATED_AT DESC
        """
    ).to_pandas()


def get_open_incident_ids():
    rows = session.sql(
        f"""
        SELECT INCIDENT_ID
        FROM {INCIDENTS_TABLE}
        WHERE STATUS = 'OPEN'
        ORDER BY CREATED_AT DESC
        """
    ).collect()
    return [row["INCIDENT_ID"] for row in rows]


def resolve_incident(incident_id, resolution_notes):
    session.sql(
        f"""
        UPDATE {INCIDENTS_TABLE}
        SET
            STATUS = 'RESOLVED',
            UPDATED_AT = CURRENT_TIMESTAMP(),
            RESOLUTION_NOTES = '{sql_escape(resolution_notes)}',
            RESOLVED_AT = CURRENT_TIMESTAMP()
        WHERE INCIDENT_ID = '{sql_escape(incident_id)}'
        """
    ).collect()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div style="font-size:2.5rem;font-weight:700;">🏭 MFG Sentinel</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="font-size:1.05rem;opacity:0.75;margin-bottom:20px;">'
    "Predictive Maintenance & Failure Diagnosis Command Center"
    "</div>",
    unsafe_allow_html=True,
)
st.write(
    "A sensor-driven command center for machine-failure prediction, "
    "failure-mode diagnosis, native incident management, and automated "
    "critical alerts."
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
    st.markdown("### Snowflake ML Stack")
    st.write("✅ Overall Failure Model")
    st.write("✅ TWF Model")
    st.write("✅ HDF Model")
    st.write("✅ PWF Model")
    st.write("✅ OSF Model")
    st.write("✅ RNF Model")

    st.divider()
    st.markdown("### Native Workflow")
    st.write("✅ Live analysis events")
    st.write("✅ KPI aggregation")
    st.write("✅ Incident register")
    st.write("✅ Critical email alert")

    st.divider()
    st.caption(
        "The available AI4I dataset does not contain the availability, "
        "performance, and quality data required for a true OEE calculation. "
        "The command center therefore does not fabricate an OEE value."
    )

if warning_threshold >= critical_threshold:
    st.error("Warning threshold must be lower than the critical threshold.")
    st.stop()

if not persistence_ready:
    st.stop()

# ============================================================
# TABS
# ============================================================

tab_live, tab_kpi, tab_incidents = st.tabs(
    ["🧪 Live Analysis", "📊 Command Center", "🚨 Incident Register"]
)

# ============================================================
# TAB 1 — LIVE ANALYSIS
# ============================================================

with tab_live:
    st.subheader("Live Machine Analysis")
    st.write(
        "The operator enters current machine conditions. The six Snowflake "
        "ML models generate overall machine risk and failure-mode diagnostics. "
        "Every analyzed observation is persisted for use by the Command Center."
    )

    c1, c2 = st.columns(2)

    with c1:
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

    with c2:
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

    temperature_delta = process_temperature - air_temperature
    power_proxy = rotational_speed * torque
    wear_torque_interaction = torque * tool_wear

    st.markdown("### 📐 Derived Machine Features")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.metric("Temperature Delta", f"{temperature_delta:.2f} K")
    with d2:
        st.metric("Power Proxy", f"{power_proxy:,.0f}")
    with d3:
        st.metric("Wear × Torque", f"{wear_torque_interaction:,.0f}")

    st.divider()

    analyze = st.button(
        "🔍 Analyze Machine",
        type="primary",
        use_container_width=True,
    )

    if analyze:
        with st.spinner("Running six predictive-maintenance models..."):
            try:
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

                failure_probability = float(result["FAILURE_PROBABILITY"])
                mode_probabilities = {
                    "TWF": float(result["TWF_PROBABILITY"]),
                    "HDF": float(result["HDF_PROBABILITY"]),
                    "PWF": float(result["PWF_PROBABILITY"]),
                    "OSF": float(result["OSF_PROBABILITY"]),
                    "RNF": float(result["RNF_PROBABILITY"]),
                }
                predicted_class = str(result["FAILURE_CLASS"])

                sensor_values = {
                    "air_temperature": air_temperature,
                    "process_temperature": process_temperature,
                    "rpm": rotational_speed,
                    "torque": torque,
                    "wear": tool_wear,
                    "temperature_delta": temperature_delta,
                    "power_proxy": power_proxy,
                    "wear_torque_interaction": wear_torque_interaction,
                }

                (
                    status,
                    diagnosis,
                    sensor_context,
                    action,
                    strongest_mode,
                ) = generate_rca(
                    failure_probability,
                    mode_probabilities,
                    sensor_values,
                    warning_threshold,
                    critical_threshold,
                )

                event_id = generate_event_id()

                save_analysis_event(
                    event_id,
                    predicted_class,
                    failure_probability,
                    mode_probabilities,
                    status,
                    strongest_mode,
                    diagnosis,
                    sensor_context,
                    action,
                    sensor_values,
                )

                st.session_state["last_event_id"] = event_id

                st.markdown("### 🚨 Overall Machine Risk")
                r1, r2, r3 = st.columns(3)

                with r1:
                    st.metric(
                        "Failure Probability",
                        f"{failure_probability*100:.2f}%",
                    )
                with r2:
                    st.metric("Risk Level", status)
                with r3:
                    st.metric("Predicted Class", predicted_class)

                st.progress(
                    min(max(failure_probability, 0.0), 1.0),
                    text=f"Failure Risk: {failure_probability*100:.2f}%",
                )

                if status == "CRITICAL":
                    st.error("🔴 CRITICAL: High machine-failure risk detected.")
                elif status == "WARNING":
                    st.warning("🟡 WARNING: Elevated machine-failure risk detected.")
                else:
                    st.success("🟢 NORMAL: No strong immediate failure signal detected.")

                st.markdown("### 🔬 Failure Mode Diagnostics")
                diagnostic_cols = st.columns(5)

                for column, (mode, probability) in zip(
                    diagnostic_cols,
                    mode_probabilities.items(),
                ):
                    with column:
                        st.metric(mode, f"{probability*100:.2f}%")
                        st.caption(MODEL_NAMES[mode])
                        st.progress(min(max(probability, 0.0), 1.0))

                st.markdown("### 🧠 Diagnostic Assessment")
                st.info(diagnosis)
                st.caption(sensor_context)

                st.markdown("### 🛠️ Recommended Action")
                if status == "CRITICAL":
                    st.error(action)
                elif status == "WARNING":
                    st.warning(action)
                else:
                    st.info(action)

                if status in ("WARNING", "CRITICAL"):
                    severity = "CRITICAL" if status == "CRITICAL" else "MEDIUM"

                    incident_id = create_incident(
                        event_id=event_id,
                        severity=severity,
                        failure_probability=failure_probability,
                        failure_class=predicted_class,
                        primary_failure_mode=strongest_mode,
                        diagnosis=diagnosis,
                        sensor_context=sensor_context,
                        action=action,
                    )

                    st.session_state["last_incident_id"] = incident_id
                    st.markdown("### 🚨 Native Incident Triage")
                    st.warning(
                        f"Incident **{incident_id}** has been created with status **OPEN**."
                    )

                    if status == "CRITICAL":
                        with st.spinner("Sending critical email alert..."):
                            try:
                                send_failure_email(
                                    failure_probability,
                                    predicted_class,
                                    mode_probabilities,
                                    strongest_mode,
                                    diagnosis,
                                    action,
                                    sensor_values,
                                    incident_id,
                                )
                                mark_email_sent(incident_id)
                                st.success(
                                    f"📧 Critical alert sent to {EMAIL_RECIPIENT}."
                                )
                            except Exception as email_error:
                                st.error(
                                    "The critical incident was created, "
                                    "but the email could not be sent."
                                )
                                with st.expander("View email error"):
                                    st.exception(email_error)
                else:
                    st.success(
                        f"Analysis event **{event_id}** recorded. "
                        "No incident was created because the machine did not "
                        "cross the warning threshold."
                    )

                with st.expander("📋 View Persisted Analysis Event"):
                    st.write(
                        {
                            "event_id": event_id,
                            "risk_level": status,
                            "failure_probability": failure_probability,
                            "primary_failure_mode": strongest_mode,
                            "stored_in": EVENTS_TABLE,
                        }
                    )

                st.caption(
                    "This new observation is now persisted in Snowflake and "
                    "will be reflected in the Command Center KPIs."
                )

            except Exception as e:
                st.error("An error occurred during machine analysis.")
                st.exception(e)

# ============================================================
# TAB 2 — COMMAND CENTER
# ============================================================

with tab_kpi:
    st.subheader("📊 Predictive Maintenance Command Center")
    st.write(
        "The Command Center combines the existing AI4I machine dataset with "
        "new observations analyzed through the Live Analysis tab. Historical "
        "failure KPIs remain grounded in observed labels, while live analyses "
        "contribute new operating-condition and risk KPIs."
    )

    try:
        historical = get_historical_kpis()
        live = get_live_kpis()
        combined = get_combined_sensor_kpis()
        failure_modes = get_failure_mode_kpis()

        st.markdown("### Fleet & Alert KPIs")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric(
                "Historical Observations",
                f"{int(historical['TOTAL_OBSERVATIONS']):,}",
            )
        with k2:
            st.metric(
                "Observed Historical Failures",
                f"{int(historical['OBSERVED_FAILURES']):,}",
            )
        with k3:
            st.metric(
                "Historical Failure Rate",
                f"{float(historical['FAILURE_RATE_PCT']):.2f}%",
            )
        with k4:
            st.metric(
                "Live Analyses",
                f"{int(live['ANALYZED_EVENTS']):,}",
            )

        k5, k6, k7, k8 = st.columns(4)

        with k5:
            st.metric("Critical Alerts", f"{int(live['CRITICAL_EVENTS']):,}")
        with k6:
            st.metric("Warning Alerts", f"{int(live['WARNING_EVENTS']):,}")
        with k7:
            st.metric(
                "Average Live Failure Risk",
                f"{float(live['AVG_LIVE_RISK_PCT']):.2f}%",
            )
        with k8:
            last_ts = live["LAST_ANALYSIS_TS"]
            st.metric(
                "Last Live Analysis",
                "No live analysis" if last_ts is None else str(last_ts)[:19],
            )

        st.markdown("### Combined Operating Profile")
        p1, p2, p3, p4 = st.columns(4)

        with p1:
            st.metric(
                "Avg Tool Wear",
                f"{float(combined['AVG_COMBINED_TOOL_WEAR_MIN']):.1f} min",
            )
        with p2:
            st.metric(
                "Avg Rotational Speed",
                f"{float(combined['AVG_COMBINED_RPM']):,.0f} RPM",
            )
        with p3:
            st.metric(
                "Avg Torque",
                f"{float(combined['AVG_COMBINED_TORQUE_NM']):.2f} Nm",
            )
        with p4:
            st.metric(
                "Avg Temperature Delta",
                f"{float(combined['AVG_COMBINED_TEMP_DELTA']):.2f} K",
            )

        st.markdown("### OEE Data Readiness")
        st.info(
            "A true OEE value is not calculated because the available AI4I "
            "dataset does not provide the availability, performance, and "
            "quality inputs needed to compute OEE without fabricating data."
        )

        o1, o2, o3 = st.columns(3)
        with o1:
            st.metric("Availability Data", "NOT AVAILABLE")
        with o2:
            st.metric("Performance Data", "NOT AVAILABLE")
        with o3:
            st.metric("Quality Data", "NOT AVAILABLE")

        st.markdown("### Historical Failure-Mode Distribution")
        mode_data = {
            "TWF": int(failure_modes["TWF_COUNT"]),
            "HDF": int(failure_modes["HDF_COUNT"]),
            "PWF": int(failure_modes["PWF_COUNT"]),
            "OSF": int(failure_modes["OSF_COUNT"]),
            "RNF": int(failure_modes["RNF_COUNT"]),
        }
        st.bar_chart(mode_data)

        st.markdown("### Live Analysis Risk Trend")
        risk_history = get_risk_history()

        if risk_history.empty:
            st.info(
                "No live analyses have been recorded yet. New observations "
                "entered in the Live Analysis tab will appear automatically."
            )
        else:
            risk_history = risk_history.set_index("EVENT_TS")
            st.line_chart(risk_history["FAILURE_RISK_PCT"])

        st.markdown("### Recent Live Analysis Events")
        recent_events = get_recent_events()

        if recent_events.empty:
            st.info("No live analysis events have been recorded.")
        else:
            st.dataframe(
                recent_events,
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            f"Historical KPIs originate from {DATABASE}.ANALYTICS.MACHINE_FEATURES. "
            f"New Streamlit observations are persisted in {EVENTS_TABLE} and "
            "are included in combined operating-profile KPIs."
        )

    except Exception as dashboard_error:
        st.error("The Command Center could not load its KPI data.")
        st.exception(dashboard_error)

# ============================================================
# TAB 3 — INCIDENT REGISTER
# ============================================================

with tab_incidents:
    st.subheader("🚨 Native Incident Register")
    st.write(
        "MFG Sentinel maintains a native incident register in Snowflake. "
        "Warning and critical analyses create incidents automatically, "
        "providing an internal triage mechanism when an external system "
        "such as Jira or ServiceNow is not connected."
    )

    try:
        status_filter = st.selectbox(
            "Incident status",
            ["ALL", "OPEN", "RESOLVED"],
        )

        incidents = get_incidents(status_filter)

        all_incidents = get_incidents("ALL")

        total_incidents = len(all_incidents)
        open_incidents = len(
            all_incidents[all_incidents["STATUS"] == "OPEN"]
        )
        critical_incidents = len(
            all_incidents[all_incidents["SEVERITY"] == "CRITICAL"]
        )
        email_alerts = len(
            all_incidents[all_incidents["EMAIL_SENT"] == True]
        )

        i1, i2, i3, i4 = st.columns(4)

        with i1:
            st.metric("Total Incidents", total_incidents)
        with i2:
            st.metric("Open Incidents", open_incidents)
        with i3:
            st.metric("Critical Incidents", critical_incidents)
        with i4:
            st.metric("Email Alerts Sent", email_alerts)

        if incidents.empty:
            st.success("No incidents match the selected status.")
        else:
            display_columns = [
                "INCIDENT_ID",
                "CREATED_AT",
                "SEVERITY",
                "STATUS",
                "FAILURE_RISK_PCT",
                "PRIMARY_FAILURE_MODE",
                "EMAIL_SENT",
            ]
            st.dataframe(
                incidents[display_columns],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.markdown("### Incident Actions")

        open_ids = get_open_incident_ids()

        if not open_ids:
            st.info("There are currently no open incidents requiring action.")
        else:
            selected_incident = st.selectbox(
                "Select an open incident",
                open_ids,
            )

            resolution_notes = st.text_area(
                "Resolution notes",
                placeholder="Enter the maintenance/triage outcome...",
            )

            if st.button(
                "✅ Mark Incident Resolved",
                use_container_width=True,
            ):
                if not resolution_notes.strip():
                    st.warning(
                        "Please enter resolution notes before resolving the incident."
                    )
                else:
                    resolve_incident(
                        selected_incident,
                        resolution_notes,
                    )
                    st.success(
                        f"Incident {selected_incident} has been marked RESOLVED."
                    )
                    st.rerun()

        st.divider()
        st.markdown("### Native Incident Lifecycle")
        st.write(
            "**OPEN → RESOLVED**  \n"
            "A warning or critical machine-analysis event creates an incident "
            "automatically. Critical incidents additionally trigger the Snowflake "
            "email notification. The maintenance outcome can then be recorded "
            "directly in the incident register."
        )
        st.caption(
            f"Incident records are stored in {INCIDENTS_TABLE}."
        )

    except Exception as incident_error:
        st.error("The Incident Register could not be loaded.")
        st.exception(incident_error)

st.divider()
st.caption(
    "MFG Sentinel | Snowflake ML + Streamlit | "
    "Sensor Intelligence → Diagnosis → Incident → Alert"
)

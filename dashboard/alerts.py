"""
IIoT SENTINEL 4.0 - Page 8: Security Alert History
Filterable industrial security incident logs, forensic metadata, and exportable alert reports.
"""

import streamlit as st
import pandas as pd
import io


def render_alerts_page(test_stream_df):
    st.markdown("## 🚨 Industrial Security Incident & Alert History")
    st.markdown("Forensic incident log compiling all flagged anomalies, intrusions, and policy deviations.")

    # Filter to anomalies & attacks
    alert_stream = test_stream_df[test_stream_df["hybrid_decision"] != "NORMAL"].copy().reset_index()
    alert_stream["Alert ID"] = [f"ALERT-IIOT-{i+1:05d}" for i in range(len(alert_stream))]
    
    # High-level counters
    total_alerts = len(alert_stream)
    critical_alerts = int((alert_stream["severity"] == "RED (CRITICAL)").sum())
    warning_alerts = int((alert_stream["severity"] == "AMBER (WARNING)").sum())

    a1, a2, a3 = st.columns(3)
    with a1:
        st.metric("Total Incident Events", f"{total_alerts:,}")
    with a2:
        st.metric("Critical Intrusion Events (Red)", f"{critical_alerts:,}", delta="Simulated Containment / Triage", delta_color="inverse")
    with a3:
        st.metric("Anomalous Events (Amber)", f"{warning_alerts:,}", delta="Autoencoder Detection", delta_color="off")

    st.markdown("---")

    # Interactive Filters
    st.subheader("Filter Security Incidents")
    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
        decisions_avail = ["All"] + list(alert_stream["hybrid_decision"].unique())
        sel_decision = st.selectbox("Filter by Decision:", decisions_avail)

    with f_col2:
        severity_avail = ["All"] + list(alert_stream["severity"].unique())
        sel_severity = st.selectbox("Filter by Severity:", severity_avail)

    with f_col3:
        attacks_avail = ["All"] + list(alert_stream["predicted_attack_type"].unique())
        sel_attack = st.selectbox("Filter by Attack Vector:", attacks_avail)

    # Apply filters
    filtered_df = alert_stream.copy()
    if sel_decision != "All":
        filtered_df = filtered_df[filtered_df["hybrid_decision"] == sel_decision]
    if sel_severity != "All":
        filtered_df = filtered_df[filtered_df["severity"] == sel_severity]
    if sel_attack != "All":
        filtered_df = filtered_df[filtered_df["predicted_attack_type"] == sel_attack]

    st.write(f"Displaying **{len(filtered_df):,} matching security alerts**:")

    # Table view
    display_cols = [
        "Alert ID", "index", "predicted_attack_type", "severity",
        "hybrid_decision", "binary_attack_probability", "reconstruction_error"
    ]
    renamed_cols = {
        "index": "Packet Seq #",
        "predicted_attack_type": "Taxonomy",
        "severity": "Severity Level",
        "hybrid_decision": "Engine Decision",
        "binary_attack_probability": "Malicious Prob",
        "reconstruction_error": "Reconstruction MSE"
    }

    final_table = filtered_df[display_cols].rename(columns=renamed_cols)
    st.dataframe(final_table, use_container_width=True, hide_index=True)

    # CSV Download
    csv_buf = io.StringIO()
    final_table.to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Export Filtered Alert History (CSV)",
        data=csv_buf.getvalue(),
        file_name="iiot_sentinel_incident_report.csv",
        mime="text/csv"
    )


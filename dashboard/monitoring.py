"""
IIoT SENTINEL 4.0 - Page 2: Simulated Traffic Monitoring
Provides interactive stream playback over held-out test traffic simulating live industrial sensor telemetry.
"""

import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def render_monitoring_page(test_stream_df):
    st.markdown("## 📡 Simulated Industrial Traffic Stream Monitoring")
    st.caption(
        "⚠️ **Simulation Notice:** This console replays held-out test records to simulate live operational network traffic. "
        "It operates purely in software without physical PLCs or industrial hardware connected."
    )

    # Initialize session state for stream playback
    if "stream_idx" not in st.session_state:
        st.session_state.stream_idx = 0
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "recent_alerts" not in st.session_state:
        st.session_state.recent_alerts = []

    # Stream Controls
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1, 1, 1, 2])
    with ctrl_col1:
        if st.button("▶️ Start Replay", use_container_width=True):
            st.session_state.is_running = True
    with ctrl_col2:
        if st.button("⏸️ Pause", use_container_width=True):
            st.session_state.is_running = False
    with ctrl_col3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.stream_idx = 0
            st.session_state.is_running = False
            st.session_state.recent_alerts = []
            st.rerun()
    with ctrl_col4:
        batch_step = st.slider("Step Size (packets per tick):", min_value=1, max_value=25, value=1)

    # Progress bar and index
    total_packets = len(test_stream_df)
    current_idx = min(st.session_state.stream_idx, total_packets - 1)
    progress_ratio = current_idx / (total_packets - 1) if total_packets > 1 else 1.0
    st.progress(progress_ratio)
    st.caption(f"Packet Sequence: **{current_idx:,} / {total_packets:,}**")

    # If stream running, advance index
    if st.session_state.is_running and current_idx < total_packets - 1:
        st.session_state.stream_idx = min(current_idx + batch_step, total_packets - 1)

    current_record = test_stream_df.iloc[current_idx]

    # Inspect current record metrics
    decision = current_record.get("hybrid_decision", "NORMAL")
    severity = current_record.get("severity", "GREEN (NORMAL)")
    atk_type = current_record.get("predicted_attack_type", "Normal")
    prob = current_record.get("binary_attack_probability", 0.0)
    recon = current_record.get("reconstruction_error", 0.0)

    # Color code card according to severity
    card_color = "#00E676" if "GREEN" in severity else ("#FF1744" if "RED" in severity else "#FF9100")
    bg_style = f"border-left: 6px solid {card_color}; background-color: #161B22; padding: 15px; border-radius: 8px; margin-bottom: 20px;"

    st.markdown(f"""
    <div style="{bg_style}">
        <h3 style="margin: 0; color: {card_color};">Status: {decision}</h3>
        <p style="margin: 5px 0 0 0; color: #8B949E;">Packet ID: #{current_idx:05d} | Severity Rating: <strong>{severity}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
    with rec_col1:
        st.metric("Binary Malicious Prob", f"{prob*100:.1f}%")
    with rec_col2:
        st.metric("Taxonomy Classification", atk_type)
    with rec_col3:
        st.metric("Reconstruction MSE", f"{recon:.4e}")
    with rec_col4:
        st.metric("Destination Port", str(current_record.get("tcp.dstport", "N/A")))

    # Track Alert History
    if decision != "NORMAL":
        alert_entry = {
            "Packet ID": f"#{current_idx:05d}",
            "Decision": decision,
            "Attack Taxonomy": atk_type,
            "Severity": severity,
            "Probability": f"{prob*100:.1f}%",
            "Reconstruction Error": f"{recon:.4e}"
        }
        if not any(a["Packet ID"] == alert_entry["Packet ID"] for a in st.session_state.recent_alerts):
            st.session_state.recent_alerts.insert(0, alert_entry)
            st.session_state.recent_alerts = st.session_state.recent_alerts[:15]

    st.markdown("---")

    # Lower Split: Real-Time Alert Log and Protocol Header Inspector
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🚨 Live Event Log (Recent Anomalies & Attacks)")
        if st.session_state.recent_alerts:
            alerts_df = pd.DataFrame(st.session_state.recent_alerts)
            st.dataframe(alerts_df, use_container_width=True, hide_index=True)
        else:
            st.info("No threats flagged in recent sequence window. Telemetry is normal.")

    with col_right:
        st.subheader("🔍 Active Packet Header Telemetry")
        # Extract protocol fields from current record
        telemetry_fields = [
            c for c in current_record.index
            if c not in ["hybrid_decision", "severity", "binary_attack_probability", "reconstruction_error", "predicted_attack_type"]
        ][:12]
        
        t_data = [{"Protocol Field": f, "Recorded Value": str(current_record[f])} for f in telemetry_fields]
        st.dataframe(pd.DataFrame(t_data), use_container_width=True, hide_index=True)

    # Auto rerun if stream is active
    if st.session_state.is_running and current_idx < total_packets - 1:
        time.sleep(0.3)
        st.rerun()


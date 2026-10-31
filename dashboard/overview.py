"""
IIoT SENTINEL 4.0 - Page 1: Security Overview
Displays global security telemetry, high-level KPIs, class distributions, and hybrid architecture status.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def render_overview_page(manifest, metrics_summary, hybrid_metrics, test_stream_df):
    st.markdown("## 🛡️ Industrial Security Operations Center — Overview")
    st.markdown(
        "Real-time situational awareness across monitored industrial control networks, edge gateways, and IoT sensor clusters."
    )

    # Status Banner
    mode = manifest.get("mode", "REAL")
    best_model = manifest.get("model_selected", "XGBoost")
    dataset_name = manifest.get("dataset_used", "Edge-IIoTset")
    
    st.info(
        f"**Engine Status:** ONLINE | **Execution Profile:** `{mode}` | "
        f"**Benchmark Dataset:** `{dataset_name}` | **Supervised Core:** `{best_model}` | "
        f"**Hybrid Decision Engine:** Active"
    )

    # High-Level Metric Cards
    hyb = hybrid_metrics
    total_records = len(test_stream_df)
    normal_count = int((test_stream_df["hybrid_decision"] == "NORMAL").sum())
    known_atk_count = int((test_stream_df["hybrid_decision"] == "KNOWN ATTACK").sum())
    unknown_atk_count = int((test_stream_df["hybrid_decision"] == "POTENTIAL UNKNOWN ATTACK").sum())
    suspicious_count = int((test_stream_df["hybrid_decision"] == "SUSPICIOUS / UNCERTAIN").sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Traffic Evaluated", f"{total_records:,}")
    with col2:
        st.metric("Legitimate Sensor Telemetry", f"{normal_count:,}", delta=f"{normal_count/total_records*100:.1f}%")
    with col3:
        st.metric("Confirmed Known Attacks", f"{known_atk_count:,}", delta="Critical Alert", delta_color="inverse")
    with col4:
        st.metric("Potential Unknown Attacks", f"{unknown_atk_count:,}", delta="Autoencoder Anomaly", delta_color="inverse")
    with col5:
        st.metric("Suspicious / Uncertain", f"{suspicious_count:,}", delta="Analyst Review", delta_color="off")

    st.markdown("---")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Attack Detection Recall", f"{hyb.get('attack_recall', 0.99)*100:.2f}%", help="Proportion of malicious traffic detected")
    with col_m2:
        st.metric("False Negative Rate (FNR)", f"{hyb.get('fnr', 0.005)*100:.3f}%", delta="Undetected Threats", delta_color="inverse")
    with col_m3:
        st.metric("False Positive Rate (FPR)", f"{hyb.get('fpr', 0.05)*100:.3f}%", delta="Nuisance Alarms", delta_color="off")
    with col_m4:
        st.metric("Macro F1-Score", f"{hyb.get('macro_f1', 0.98)*100:.2f}%", help="Balanced harmonic mean across normal and attack classes")

    st.markdown("---")

    # Visualizations
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Hybrid Triage Decision Breakdown")
        decision_counts = test_stream_df["hybrid_decision"].value_counts().reset_index()
        decision_counts.columns = ["Decision", "Count"]

        color_map = {
            "NORMAL": "#00E676",
            "KNOWN ATTACK": "#FF1744",
            "POTENTIAL UNKNOWN ATTACK": "#FF9100",
            "SUSPICIOUS / UNCERTAIN": "#FFD600"
        }

        fig_decision = px.pie(
            decision_counts,
            names="Decision",
            values="Count",
            color="Decision",
            color_discrete_map=color_map,
            hole=0.45
        )
        fig_decision.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6EDF3")
        )
        st.plotly_chart(fig_decision, use_container_width=True)

    with chart_col2:
        st.subheader("Detected Attack Taxonomy Distribution")
        atk_df = test_stream_df[test_stream_df["predicted_attack_type"] != "Normal"]
        if not atk_df.empty:
            atk_counts = atk_df["predicted_attack_type"].value_counts().reset_index()
            atk_counts.columns = ["Attack Taxonomy", "Count"]
            
            fig_atk = px.bar(
                atk_counts,
                x="Count",
                y="Attack Taxonomy",
                orientation="h",
                color="Count",
                color_continuous_scale="Reds"
            )
            fig_atk.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E6EDF3"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_atk, use_container_width=True)
        else:
            st.info("No attack packets in current sample subset.")

    # Architectural Overview
    st.subheader("Hybrid Decision Architecture Summary")
    st.markdown("""
    ```
    Industrial Packet Capture
               │
               ▼
    Feature Imputation & Robust Scaling (Fitted on Train Only)
               │
        ┌──────┴─────────────────────────────────┐
        ▼                                        ▼
    Supervised Classifier (XGBoost/RF)     Autoencoder (Normal-Trained Only)
    Known Threat Signatures               Reconstruction Variance from Benign Baseline
        │                                        │
        └──────┬─────────────────────────────────┘
               ▼
        Hybrid Decision Engine (4-Case Triage Matrix)
        ├─ NORMAL                     (P(Atk) < Thresh & Error <= AE_Thresh)
        ├─ KNOWN ATTACK               (P(Atk) >= Thresh)
        ├─ POTENTIAL UNKNOWN ATTACK   (P(Atk) < Thresh & Error > AE_Thresh)
        └─ SUSPICIOUS / UNCERTAIN     (Boundary Probability & Elevated Variance)
    ```
    """)


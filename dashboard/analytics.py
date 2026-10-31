"""
IIoT SENTINEL 4.0 - Page 3: Attack Analytics
Visualizes attack distributions, per-class metrics, taxonomy clustering, and interactive confusion matrices.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


# Attack categories for IIoT taxonomic clustering
ATTACK_CATEGORIES = {
    "Normal": "Benign Telemetry",
    "DDoS_UDP": "Denial of Service (DoS)",
    "DDoS_ICMP": "Denial of Service (DoS)",
    "DDoS_TCP": "Denial of Service (DoS)",
    "DDoS_HTTP": "Denial of Service (DoS)",
    "SQL_injection": "Web Injection",
    "XSS": "Web Injection",
    "Uploading": "Web Exploit",
    "Ransomware": "Malware & Ransomware",
    "Backdoor": "Persistence & Trojan",
    "Password": "Credential Theft",
    "Port_Scanning": "Reconnaissance",
    "Vulnerability_scanner": "Reconnaissance",
    "Fingerprinting": "Reconnaissance",
    "MITM": "Man-In-The-Middle"
}


def render_analytics_page(per_class_report, multiclass_cm, classes_list, test_stream_df):
    st.markdown("## 📊 Comprehensive Attack Analytics & Threat Profiling")
    st.markdown("Forensic taxonomy breakdown across industrial protocols, sensor attacks, and reconnaissance sweeps.")

    # High-level summary
    atk_only = test_stream_df[test_stream_df["predicted_attack_type"] != "Normal"]
    most_common_atk = atk_only["predicted_attack_type"].mode().iloc[0] if not atk_only.empty else "N/A"
    most_common_count = (test_stream_df["predicted_attack_type"] == most_common_atk).sum()

    top_c1, top_c2, top_c3, top_c4 = st.columns(4)
    with top_c1:
        st.metric("Total Attack Instances Detected", f"{len(atk_only):,}")
    with top_c2:
        st.metric("Unique Threat Profiles", f"{len(classes_list) - 1}")
    with top_c3:
        st.metric("Predominant Attack Vector", most_common_atk)
    with top_c4:
        st.metric("Top Vector Volume", f"{most_common_count:,}", delta=f"{most_common_count/len(test_stream_df)*100:.1f}% of traffic")

    st.markdown("---")

    # Visualizations: Threat Frequency and Taxonomic Clustering
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Threat Frequency by Specific Class")
        if not atk_only.empty:
            type_counts = atk_only["predicted_attack_type"].value_counts().reset_index()
            type_counts.columns = ["Attack Type", "Detections"]
            fig_types = px.bar(
                type_counts,
                x="Detections",
                y="Attack Type",
                orientation="h",
                color="Detections",
                color_continuous_scale="Viridis"
            )
            fig_types.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E6EDF3"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_types, use_container_width=True)

    with col2:
        st.subheader("Threat Volume by High-Level Category")
        category_series = test_stream_df["predicted_attack_type"].map(ATTACK_CATEGORIES).fillna("Other")
        cat_counts = category_series.value_counts().reset_index()
        cat_counts.columns = ["Category", "Volume"]

        fig_cat = px.pie(
            cat_counts,
            names="Category",
            values="Volume",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_cat.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6EDF3")
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("---")

    # Per-Class Precision, Recall, F1 Table
    st.subheader("📋 Per-Class Performance Breakdown")
    class_rows = []
    for cls_name in classes_list:
        if cls_name in per_class_report:
            m = per_class_report[cls_name]
            class_rows.append({
                "Taxonomy": cls_name,
                "Category": ATTACK_CATEGORIES.get(cls_name, "Security Threat"),
                "Precision": f"{m.get('precision', 0.0)*100:.2f}%",
                "Recall (Sensitivity)": f"{m.get('recall', 0.0)*100:.2f}%",
                "F1-Score": f"{m.get('f1-score', 0.0)*100:.2f}%",
                "Test Support": int(m.get("support", 0))
            })

    if class_rows:
        class_table_df = pd.DataFrame(class_rows)
        st.dataframe(class_table_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Interactive Multiclass Confusion Matrix
    st.subheader("🎯 Multiclass Confusion Matrix Heatmap")
    st.caption("Rows represent actual ground-truth classes; columns represent model predictions.")

    if multiclass_cm and len(classes_list) > 0:
        cm_arr = np.array(multiclass_cm)
        fig_cm = px.imshow(
            cm_arr,
            x=classes_list,
            y=classes_list,
            color_continuous_scale="Blues",
            labels=dict(x="Predicted Taxonomy", y="Actual Ground Truth", color="Sample Count"),
            text_auto=True
        )
        fig_cm.update_layout(
            margin=dict(l=30, r=30, t=30, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6EDF3"),
            xaxis=dict(tickangle=45)
        )
        st.plotly_chart(fig_cm, use_container_width=True)


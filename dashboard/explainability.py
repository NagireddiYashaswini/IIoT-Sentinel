"""
IIoT SENTINEL 4.0 - Page 6: AI Explainability
Provides global and local feature importance via SHAP and Autoencoder feature attribution.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def render_explainability_page(shap_global, shap_per_class, shap_sample_bundle, feature_columns):
    st.markdown("## 🔍 AI Explainability & Root-Cause Attribution")
    st.markdown(
        "Interpreting AI predictions through **SHapley Additive exPlanations (SHAP)** for the supervised model, "
        "and **Reconstruction Error Feature Attribution** for the unsupervised Autoencoder."
    )

    # Explanation Distinction Notice
    st.info(
        "💡 **Methodology Clarity:**\n"
        "- **SHAP** explains how input features influenced the **Supervised Model's** attack classification probability.\n"
        "- **Reconstruction Differences** explain which features deviated most from the **Autoencoder's** learned normal manifold."
    )

    tab1, tab2, tab3 = st.tabs(["🌐 Global Feature Importance", "🏷️ Per-Attack Taxonomy Importance", "🔬 Individual Packet Drilldown"])

    # Tab 1: Global SHAP Importance
    with tab1:
        st.subheader("Global Feature Importance Ranking (Supervised Classifier)")
        if shap_global:
            shap_df = pd.DataFrame(shap_global).head(15)
            fig_global = px.bar(
                shap_df,
                x="importance",
                y="feature",
                orientation="h",
                color="importance",
                color_continuous_scale="Teal",
                labels={"importance": "Mean |SHAP Value| (Impact on Malicious Probability)", "feature": "Network Feature"}
            )
            fig_global.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E6EDF3"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_global, use_container_width=True)

            st.markdown("""
            **Key Cyber Domain Observations:**
            - **`tcp.dstport`:** Destination port is heavily weighted due to attack targeting specific service endpoints (Port 80/443 for web exploits, Port 502 for Modbus, Port 22 for brute-force).
            - **`tcp.ack` & `tcp.seq`:** Packet sequence and acknowledgment metrics identify volumetric DDoS floods and out-of-order injection attacks.
            - **`icmp.checksum`:** Identifies packet tampering and ping floods.
            """)
        else:
            st.info("Global SHAP data not found in artifacts.")

    # Tab 2: Per-Class Importance
    with tab2:
        st.subheader("Taxonomy-Specific Feature Drivers")
        if shap_per_class:
            selected_class = st.selectbox("Select Attack Taxonomy to Inspect:", list(shap_per_class.keys()))
            class_features = shap_per_class.get(selected_class, [])
            if class_features:
                class_df = pd.DataFrame(class_features)
                fig_class = px.bar(
                    class_df,
                    x="importance",
                    y="feature",
                    orientation="h",
                    color="importance",
                    color_continuous_scale="Sunset",
                    labels={"importance": "Mean |SHAP Value| for Class", "feature": "Feature"}
                )
                fig_class.update_layout(
                    margin=dict(l=20, r=20, t=30, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E6EDF3"),
                    yaxis=dict(autorange="reversed")
                )
                st.plotly_chart(fig_class, use_container_width=True)
            else:
                st.info(f"No specific SHAP attributions recorded for {selected_class}.")
        else:
            st.info("Per-class SHAP attributions not present in artifacts.")

    # Tab 3: Individual Packet Drilldown
    with tab3:
        st.subheader("Microscopic Packet Root-Cause Analysis")
        if shap_sample_bundle and "shap_values" in shap_sample_bundle:
            sv_arr = shap_sample_bundle["shap_values"]
            feats_arr = shap_sample_bundle["features"]
            fnames = shap_sample_bundle["feature_names"].tolist()

            sample_idx = st.slider("Select Sample Record Index:", 0, min(len(sv_arr) - 1, 100), 0)

            rec_sv = sv_arr[sample_idx]
            rec_feats = feats_arr[sample_idx]

            # Top positive and negative contributors
            top_indices = np.argsort(np.abs(rec_sv))[::-1][:8]
            drilldown_rows = []
            for idx in top_indices:
                drilldown_rows.append({
                    "Feature": fnames[idx],
                    "Processed Value": round(float(rec_feats[idx]), 3),
                    "SHAP Impact": round(float(rec_sv[idx]), 4),
                    "Direction": "Pushes Toward ATTACK (+)" if rec_sv[idx] > 0 else "Pushes Toward NORMAL (-)"
                })

            df_drill = pd.DataFrame(drilldown_rows)

            fig_local = px.bar(
                df_drill,
                x="SHAP Impact",
                y="Feature",
                orientation="h",
                color="Direction",
                color_discrete_map={"Pushes Toward ATTACK (+)": "#FF1744", "Pushes Toward NORMAL (-)": "#00E676"}
            )
            fig_local.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E6EDF3"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_local, use_container_width=True)

            st.dataframe(df_drill, use_container_width=True, hide_index=True)
        else:
            st.info("Individual SHAP sample values not available in artifact bundle.")


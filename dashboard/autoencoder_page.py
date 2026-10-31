"""
IIoT SENTINEL 4.0 - Page 5: Autoencoder Anomaly Monitoring
Displays neural Autoencoder architecture, loss convergence, reconstruction error distributions, and anomaly thresholds.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def render_autoencoder_page(autoencoder_metrics, recon_df, training_history):
    st.markdown("## 🧠 Deep Learning Autoencoder Anomaly Monitoring")
    st.markdown(
        "The Autoencoder operates as an **unsupervised normal-behavior model**, trained strictly on legitimate industrial sensor "
        "telemetry to detect structural deviations, zero-days, and novel cyber threats."
    )

    # High-level metrics
    selected_thresh = autoencoder_metrics.get("selected_threshold", 0.130980)
    p95_thresh = autoencoder_metrics.get("p95_threshold", 0.099337)
    pct_label = autoencoder_metrics.get("selected_threshold_percentile", "p99.0")
    thresh_dict = autoencoder_metrics.get("thresholds", {})
    mean_val_loss = autoencoder_metrics.get("mean_val_loss", 0.0)

    ae_c1, ae_c2, ae_c3, ae_c4 = st.columns(4)
    with ae_c1:
        st.metric("Architecture", "PyTorch 5-Layer Autoencoder")
    with ae_c2:
        st.metric("Trained On", "Normal-Only Traffic", help="Zero attack records exposed during training")
    with ae_c3:
        st.metric(f"Active Threshold ({pct_label})", f"{selected_thresh:.6f}", help="Tuned on validation normal traffic to satisfy FPR <= 5%")
    with ae_c4:
        st.metric("Comparison Threshold (p95)", f"{p95_thresh:.6f}", help="Optional higher-sensitivity baseline (elevated false alarms)")

    st.markdown("---")

    # Training Loss Curve & Reconstruction Error Distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📉 Autoencoder Training & Validation Loss Curve")
        train_loss = training_history.get("train_loss", [])
        val_loss = training_history.get("val_loss", [])

        if train_loss and val_loss:
            epochs = list(range(1, len(train_loss) + 1))
            fig_loss = go.Figure()
            fig_loss.add_trace(go.Scatter(x=epochs, y=train_loss, mode="lines+markers", name="Train MSE Loss", line=dict(color="#00E5FF", width=2)))
            fig_loss.add_trace(go.Scatter(x=epochs, y=val_loss, mode="lines+markers", name="Validation MSE Loss (Normal Only)", line=dict(color="#FFD600", width=2)))

            fig_loss.update_layout(
                xaxis_title="Epoch",
                yaxis_title="Mean Squared Error (Reconstruction Loss)",
                yaxis_type="log",
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E6EDF3"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_loss, use_container_width=True)
        else:
            st.info("Training history not recorded in current artifact bundle.")

    with col2:
        st.subheader("📊 Reconstruction Error Distribution (Normal vs Attack)")
        if not recon_df.empty and "reconstruction_error" in recon_df.columns:
            # Subsample for smooth rendering
            sample_recon = recon_df.sample(min(2000, len(recon_df)), random_state=42).copy()
            sample_recon["Traffic Type"] = sample_recon["is_normal"].apply(lambda n: "Legitimate Normal" if n == 1 else "Malicious Attack")

            # Log scale for visualization of heavy tail
            sample_recon["log_recon_error"] = np.log10(sample_recon["reconstruction_error"] + 1e-12)

            fig_dist = px.histogram(
                sample_recon,
                x="log_recon_error",
                color="Traffic Type",
                barmode="overlay",
                nbins=40,
                color_discrete_map={"Legitimate Normal": "#00E676", "Malicious Attack": "#FF1744"}
            )
            fig_dist.update_layout(
                xaxis_title="Log10 Reconstruction Error (MSE)",
                yaxis_title="Sample Frequency",
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E6EDF3"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_dist, use_container_width=True)

    st.markdown("---")

    # Threshold Selection Sandbox
    st.subheader("🎚️ Anomaly Threshold Sensitivity Tuning")
    st.caption("Thresholds calculated strictly on NORMAL validation records. Modifying threshold shifts operational sensitivity.")

    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        threshold_options = list(thresh_dict.keys()) if thresh_dict else ["p90.0", "p95.0", "p99.0", "p99.9"]
        selected_p = st.selectbox(
            "Select Validation Percentile Threshold:",
            threshold_options,
            index=threshold_options.index("p95.0") if "p95.0" in threshold_options else 0
        )
        custom_thresh = thresh_dict.get(selected_p, selected_thresh)
        st.markdown(f"**Reconstruction Threshold Value:** `{custom_thresh:.4e}`")

    with col_t2:
        if not recon_df.empty:
            anom_count = int((recon_df["reconstruction_error"] > custom_thresh).sum())
            anom_pct = anom_count / len(recon_df) * 100
            st.info(
                f"At **{selected_p}** threshold (`{custom_thresh:.4e}`), **{anom_count:,} packets ({anom_pct:.2f}%)** "
                f"in the test evaluation stream are flagged as anomalies requiring security inspection."
            )

    st.markdown("---")

    # Neural Architecture Inspection
    st.subheader("📐 PyTorch Symmetric Autoencoder Architecture")
    st.markdown("""
    ```
    Input Layer: Processed Features (D-dim: 44-47 features)
        │
        ▼
    Encoder Dense Layer 1: Linear(D -> 128) + BatchNorm + ReLU
        │
        ▼
    Encoder Dense Layer 2: Linear(128 -> 64) + BatchNorm + ReLU
        │
        ▼
    Latent Bottleneck: Linear(64 -> 16) + ReLU  <-- Compressed Industrial Manifold
        │
        ▼
    Decoder Dense Layer 1: Linear(16 -> 64) + BatchNorm + ReLU
        │
        ▼
    Decoder Dense Layer 2: Linear(64 -> 128) + BatchNorm + ReLU
        │
        ▼
    Output Layer: Linear(128 -> D) (Mean Squared Error Reconstruction Loss)
    ```
    """)


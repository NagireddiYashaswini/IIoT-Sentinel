"""
IIoT SENTINEL 4.0 — Hybrid Industrial IoT Intrusion Detection & Anomaly Monitoring System
Main Streamlit Multi-Page Application.
"""

import os
import tempfile
from pathlib import Path

# Workspace directories
APP_DIR = Path(__file__).resolve().parent
STREAMLIT_DIR = APP_DIR / ".streamlit"
os.environ.setdefault("STREAMLIT_CONFIG_DIR", str(STREAMLIT_DIR))
os.environ.setdefault("STREAMLIT_CREDENTIALS_FILE", str(STREAMLIT_DIR / "credentials.toml"))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import streamlit as st
import joblib
import torch
import numpy as np
import pandas as pd
from pathlib import Path

import config
from utils import load_json, logger
from src.autoencoder import AutoencoderAnomalyDetector, PyTorchAutoencoder

# Page renderers
from dashboard.overview import render_overview_page
from dashboard.monitoring import render_monitoring_page
from dashboard.analytics import render_analytics_page
from dashboard.false_negatives import render_false_negatives_page
from dashboard.autoencoder_page import render_autoencoder_page
from dashboard.explainability import render_explainability_page
from dashboard.new_data import render_new_data_page
from dashboard.alerts import render_alerts_page
from dashboard.model_performance import render_model_performance_page

# Set page configuration
st.set_page_config(
    page_title="IIoT Sentinel 4.0 | Industrial Intrusion Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_all_models():
    """Load pre-trained models and preprocessing pipelines without re-running training."""
    models_dir = config.MODELS_DIR
    if not (models_dir / "supervised_model.joblib").exists():
        return None

    supervised_model = joblib.load(models_dir / "supervised_model.joblib")
    multiclass_model = joblib.load(models_dir / "multiclass_model.joblib")
    preprocessor = joblib.load(models_dir / "preprocessing_pipeline.joblib")
    label_encoder = joblib.load(models_dir / "label_encoder.joblib")
    
    # Load Autoencoder PyTorch model
    ae_meta = load_json(config.METRICS_DIR / "autoencoder_metrics.json")
    feature_columns = load_json(models_dir / "feature_columns.json")
    
    input_dim = len(feature_columns)
    ae_detector = AutoencoderAnomalyDetector(input_dim=input_dim)
    ae_detector.model.load_state_dict(torch.load(models_dir / "autoencoder.pt", map_location=ae_detector.device, weights_only=True))
    ae_detector.model.eval()
    ae_detector.thresholds = load_json(config.AUTOENCODER_DIR / "thresholds.json") or {}
    ae_detector.selected_threshold = ae_meta.get("selected_threshold", 1.0) if ae_meta else 1.0
    ae_detector.is_fitted = True

    return {
        "supervised_model": supervised_model,
        "multiclass_model": multiclass_model,
        "preprocessor": preprocessor,
        "label_encoder": label_encoder,
        "autoencoder_detector": ae_detector,
        "feature_columns": feature_columns
    }


@st.cache_data
def load_all_artifacts():
    """Load JSON metrics, parquet streams, and explainability bundles."""
    if not (config.ARTIFACTS_DIR / "run_manifest.json").exists():
        return None

    manifest = load_json(config.ARTIFACTS_DIR / "run_manifest.json")
    metrics_summary = load_json(config.METRICS_DIR / "metrics_summary.json")
    per_class_report = load_json(config.METRICS_DIR / "per_class_report.json")
    multiclass_cm = load_json(config.METRICS_DIR / "confusion_matrix_multiclass.json")
    hybrid_metrics = load_json(config.METRICS_DIR / "hybrid_metrics.json")
    autoencoder_metrics = load_json(config.METRICS_DIR / "autoencoder_metrics.json")
    shap_global = load_json(config.EXPLAIN_DIR / "shap_global.json")
    shap_per_class = load_json(config.EXPLAIN_DIR / "shap_per_class.json")
    training_history = load_json(config.AUTOENCODER_DIR / "training_history.json")
    classes_list = load_json(config.MODELS_DIR / "classes.json")
    
    # Parquet Data Streams
    test_stream_df = pd.read_parquet(config.DATA_ARTIFACTS_DIR / "test_stream.parquet")
    recon_df = pd.read_parquet(config.AUTOENCODER_DIR / "recon_errors.parquet")

    # Sample SHAP NPZ
    shap_sample = None
    npz_path = config.EXPLAIN_DIR / "shap_sample.npz"
    if npz_path.exists():
        with np.load(npz_path, allow_pickle=True) as data:
            shap_sample = {k: data[k] for k in data.files}

    return {
        "manifest": manifest,
        "metrics_summary": metrics_summary,
        "per_class_report": per_class_report,
        "multiclass_cm": multiclass_cm,
        "hybrid_metrics": hybrid_metrics,
        "autoencoder_metrics": autoencoder_metrics,
        "shap_global": shap_global,
        "shap_per_class": shap_per_class,
        "training_history": training_history,
        "classes_list": classes_list,
        "test_stream_df": test_stream_df,
        "recon_df": recon_df,
        "shap_sample": shap_sample
    }


def main():
    # Sidebar Branding
    st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color: #00E5FF; margin: 0;'>🛡️ IIoT SENTINEL 4.0</h2>
        <p style='color: #8B949E; font-size: 0.85em; margin: 2px 0 0 0;'>Hybrid Industrial Intrusion Detection</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Load Artifacts
    artifacts = load_all_artifacts()
    models = load_all_models()

    if artifacts is None or models is None:
        st.error("⚠️ Trained artifacts not found! Please run the training pipeline first.")
        st.info("Execute in your terminal:\n```bash\npython train.py --fast\n# or\npython train.py --demo\n```")
        return

    manifest = artifacts["manifest"]
    mode = manifest.get("mode", "REAL")

    # Sidebar Navigation Menu
    pages = [
        "🛡️ Security Overview",
        "📡 Simulated Traffic Monitoring",
        "📊 Attack Analytics",
        "🎯 False Negative Analysis",
        "🧠 Autoencoder Anomaly Monitoring",
        "🔍 AI Explainability",
        "📤 Test with New Data",
        "🚨 Security Alert History",
        "⚡ Model Performance"
    ]

    selected_page = st.sidebar.radio("Navigation Console:", pages, index=0)

    # Sidebar Telemetry Badge
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Execution Mode:** `{mode}`")
    st.sidebar.markdown(f"**Supervised Model:** `{manifest.get('model_selected', 'XGBoost')}`")
    st.sidebar.markdown(f"**Optimal Threshold:** `{manifest.get('best_threshold', 0.5):.3f}`")
    ae_pct = manifest.get('autoencoder_threshold_percentile', 'p99.0')
    st.sidebar.markdown(f"**AE Threshold ({ae_pct}):** `{manifest.get('autoencoder_threshold', 1.0):.4f}`")
    st.sidebar.markdown(f"**Evaluated Packets:** `{manifest.get('test_sample_size', 0):,}`")

    # Page Routing
    if selected_page == "🛡️ Security Overview":
        render_overview_page(
            manifest=manifest,
            metrics_summary=artifacts["metrics_summary"],
            hybrid_metrics=artifacts["hybrid_metrics"],
            test_stream_df=artifacts["test_stream_df"]
        )

    elif selected_page == "📡 Simulated Traffic Monitoring":
        render_monitoring_page(test_stream_df=artifacts["test_stream_df"])

    elif selected_page == "📊 Attack Analytics":
        render_analytics_page(
            per_class_report=artifacts["per_class_report"],
            multiclass_cm=artifacts["multiclass_cm"],
            classes_list=artifacts["classes_list"],
            test_stream_df=artifacts["test_stream_df"]
        )

    elif selected_page == "🎯 False Negative Analysis":
        render_false_negatives_page(
            metrics_summary=artifacts["metrics_summary"],
            hybrid_metrics=artifacts["hybrid_metrics"],
            test_stream_df=artifacts["test_stream_df"]
        )

    elif selected_page == "🧠 Autoencoder Anomaly Monitoring":
        render_autoencoder_page(
            autoencoder_metrics=artifacts["autoencoder_metrics"],
            recon_df=artifacts["recon_df"],
            training_history=artifacts["training_history"]
        )

    elif selected_page == "🔍 AI Explainability":
        render_explainability_page(
            shap_global=artifacts["shap_global"],
            shap_per_class=artifacts["shap_per_class"],
            shap_sample_bundle=artifacts["shap_sample"],
            feature_columns=models["feature_columns"]
        )

    elif selected_page == "📤 Test with New Data":
        render_new_data_page(
            preprocessor=models["preprocessor"],
            supervised_model=models["supervised_model"],
            multiclass_model=models["multiclass_model"],
            label_encoder=models["label_encoder"],
            autoencoder_detector=models["autoencoder_detector"],
            feature_columns=models["feature_columns"]
        )

    elif selected_page == "🚨 Security Alert History":
        render_alerts_page(test_stream_df=artifacts["test_stream_df"])

    elif selected_page == "⚡ Model Performance":
        render_model_performance_page(
            manifest=manifest,
            metrics_summary=artifacts["metrics_summary"],
            hybrid_metrics=artifacts["hybrid_metrics"],
            autoencoder_metrics=artifacts["autoencoder_metrics"]
        )


if __name__ == "__main__":
    main()

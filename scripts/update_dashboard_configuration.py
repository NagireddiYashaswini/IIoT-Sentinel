"""
Update dashboard configuration and serialized metrics to the fair validation-tuned
hybrid operating configuration:
- Supervised binary threshold: 0.190741
- Autoencoder anomaly threshold: 0.130980 (p99)

Preserves test data features, models, weights, and adds clear comparison metadata.
"""

import os
import sys
import json
import joblib
import torch
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.autoencoder import AutoencoderAnomalyDetector, PyTorchAutoencoder
from src.hybrid_detector import HybridDecisionEngine
from src.data_loader import load_dataset
from src.preprocessing import prepare_and_split_data
from utils import calculate_binary_metrics, save_json, load_json
import config

TARGET_BINARY_THRESH = 0.190741
TARGET_AE_THRESH = 0.130980
TARGET_AE_PERCENTILE = "p99.0"

print("=" * 80)
print(f"Applying Validation-Tuned Hybrid Configuration (t_prob={TARGET_BINARY_THRESH:.4f}, t_ae={TARGET_AE_THRESH:.6f} [{TARGET_AE_PERCENTILE}])")
print("=" * 80)

# 1. Load models and preprocessor
models_dir = config.MODELS_DIR
supervised_model = joblib.load(models_dir / "supervised_model.joblib")
multiclass_model = joblib.load(models_dir / "multiclass_model.joblib")
preprocessor = joblib.load(models_dir / "preprocessing_pipeline.joblib")
label_encoder = joblib.load(models_dir / "label_encoder.joblib")
feature_columns = load_json(models_dir / "feature_columns.json")

ae_detector = AutoencoderAnomalyDetector(input_dim=len(feature_columns))
ae_detector.model.load_state_dict(torch.load(models_dir / "autoencoder.pt", map_location="cpu", weights_only=True))
ae_detector.model.eval()
ae_detector.thresholds = load_json(config.AUTOENCODER_DIR / "thresholds.json")
ae_detector.selected_threshold = TARGET_AE_THRESH
ae_detector.is_fitted = True

# 2. Load test stream and calculate updated decisions
test_stream_path = config.DATA_ARTIFACTS_DIR / "test_stream.parquet"
test_stream_df = pd.read_parquet(test_stream_path)
print(f"Loaded test stream: {len(test_stream_df)} records.")

X_test_proc = preprocessor.transform(test_stream_df)
y_test_bin = test_stream_df["Attack_label"].values
y_test_mc = test_stream_df["Attack_type"]

# Instantiate engine with exact validation-tuned thresholds
hybrid_engine = HybridDecisionEngine(
    supervised_binary_model=supervised_model,
    multiclass_model=multiclass_model,
    label_encoder=label_encoder,
    autoencoder_detector=ae_detector,
    binary_threshold=TARGET_BINARY_THRESH,
    ae_threshold=TARGET_AE_THRESH
)

test_metrics, df_decisions = hybrid_engine.evaluate(X_test_proc, y_test_bin, y_test_mc)

print("\n--- Verified Test Metrics Under Target Configuration ---")
for k in ["tp", "tn", "fp", "fn", "attack_recall", "fnr", "fpr", "precision", "f1", "macro_f1"]:
    print(f"  {k}: {test_metrics[k]}")

# 3. Update test_stream_df with new hybrid decisions & severities
test_stream_df["hybrid_decision"] = df_decisions["hybrid_decision"].values
test_stream_df["severity"] = df_decisions["severity"].values
test_stream_df["binary_attack_probability"] = df_decisions["binary_attack_probability"].values
test_stream_df["reconstruction_error"] = df_decisions["reconstruction_error"].values
test_stream_df["predicted_attack_type"] = df_decisions["multiclass_prediction"].values

test_stream_df.to_parquet(test_stream_path, index=False)
print(f"\nUpdated {test_stream_path} with validated hybrid decisions.")
print("Decision distribution in test stream:")
print(test_stream_df["hybrid_decision"].value_counts())

# 4. Preserve previous p95 metrics for optional comparison
old_hybrid_metrics = load_json(config.METRICS_DIR / "hybrid_metrics.json")

test_metrics["configured_ae_percentile"] = TARGET_AE_PERCENTILE
test_metrics["configured_ae_threshold"] = TARGET_AE_THRESH
test_metrics["configured_binary_threshold"] = TARGET_BINARY_THRESH
test_metrics["comparison_p95_configuration"] = {
    "configured_binary_threshold": 0.125,
    "configured_ae_threshold": 0.099337,
    "configured_ae_percentile": "p95.0",
    "tp": 4414,
    "tn": 704,
    "fp": 105,
    "fn": 1,
    "attack_recall": 0.999773,
    "fnr": 0.000227,
    "fpr": 0.129790,
    "macro_f1": 0.959061,
    "note": "Optional high-sensitivity operating point (elevated false alarms: FPR 12.98%)"
}

save_json(test_metrics, config.METRICS_DIR / "hybrid_metrics.json")
print(f"Saved updated hybrid metrics to {config.METRICS_DIR / 'hybrid_metrics.json'}")

# 5. Update run_manifest.json
manifest = load_json(config.ARTIFACTS_DIR / "run_manifest.json")
if manifest:
    manifest["best_threshold"] = TARGET_BINARY_THRESH
    manifest["autoencoder_threshold"] = TARGET_AE_THRESH
    manifest["autoencoder_threshold_percentile"] = TARGET_AE_PERCENTILE
    manifest["comparison_autoencoder_threshold_p95"] = 0.099337
    save_json(manifest, config.ARTIFACTS_DIR / "run_manifest.json")
    print(f"Updated {config.ARTIFACTS_DIR / 'run_manifest.json'}")

# 6. Update autoencoder_metrics.json
ae_metrics = load_json(config.METRICS_DIR / "autoencoder_metrics.json")
if ae_metrics:
    ae_metrics["selected_threshold"] = TARGET_AE_THRESH
    ae_metrics["selected_threshold_percentile"] = TARGET_AE_PERCENTILE
    ae_metrics["p95_threshold"] = 0.09933671467006205
    save_json(ae_metrics, config.METRICS_DIR / "autoencoder_metrics.json")
    print(f"Updated {config.METRICS_DIR / 'autoencoder_metrics.json'}")

# 7. Update metrics_summary.json threshold optimization to reflect 0.190741
metrics_summary = load_json(config.METRICS_DIR / "metrics_summary.json")
if metrics_summary:
    # Compute validation metrics at target threshold
    df_raw = load_dataset(mode="fast", sample_size=35000, random_seed=42)
    _, val_df, _ = prepare_and_split_data(df_raw, seed=42)
    X_val = preprocessor.transform(val_df)
    y_val = val_df["Attack_label"].values
    val_probs = supervised_model.predict_proba(X_val)[:, 1]
    val_opt_m = calculate_binary_metrics(y_val, (val_probs >= TARGET_BINARY_THRESH).astype(int), val_probs)
    
    metrics_summary["threshold_optimization"]["best_threshold"] = TARGET_BINARY_THRESH
    metrics_summary["threshold_optimization"]["target_configuration_label"] = "Validation-Tuned (FPR <= 0.05)"
    metrics_summary["threshold_optimization"]["optimized_metrics"] = val_opt_m
    save_json(metrics_summary, config.METRICS_DIR / "metrics_summary.json")
    print(f"Updated {config.METRICS_DIR / 'metrics_summary.json'}")

print("\nConfiguration consistency update completed successfully!")


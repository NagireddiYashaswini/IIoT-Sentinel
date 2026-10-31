"""
Generate Final Numerical Verification Data for Tasks 1, 2, and 3.
All calculations use exact saved models, test data, and validation data.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
import torch
import xgboost as xgb

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.data_loader import load_dataset
from src.preprocessing import prepare_and_split_data
from src.autoencoder import PyTorchAutoencoder, AutoencoderAnomalyDetector
from utils import calculate_binary_metrics
import config

# Paths
DATA_DIR = "artifacts/data"
MODELS_DIR = "artifacts/models"
METRICS_DIR = "artifacts/metrics"
AE_DIR = "artifacts/autoencoder"
os.makedirs(METRICS_DIR, exist_ok=True)

# 1. Load test stream and models
print("Loading test stream...")
test_stream = pd.read_parquet(os.path.join(DATA_DIR, "test_stream.parquet"))
print(f"Test stream loaded: {len(test_stream)} records.")

prep = joblib.load(os.path.join(MODELS_DIR, "preprocessing_pipeline.joblib"))
sup_model = joblib.load(os.path.join(MODELS_DIR, "supervised_model.joblib"))

with open(os.path.join(AE_DIR, "thresholds.json"), "r") as f:
    ae_thresholds = json.load(f)

# Load test labels, probs, and errors from saved test_stream
y_test = test_stream["Attack_label"].values
test_probs = test_stream["binary_attack_probability"].values
test_recon_errors = test_stream["reconstruction_error"].values

# Also compute p80 threshold from validation normal traffic
# Let's load the full dataset to get exact validation data split
print("Loading dataset to obtain exact validation set...")
df = load_dataset(mode="fast", sample_size=35000, random_seed=42)
train_df, val_df, test_df = prepare_and_split_data(df, seed=42)

# Verify test_df matches test_stream
assert len(test_df) == len(test_stream), "Test DF length mismatch!"
print(f"Validation set size: {len(val_df)} records (Normal: {(val_df['Attack_label']==0).sum()}, Attack: {(val_df['Attack_label']==1).sum()})")

# Transform validation data
X_val = prep.transform(val_df)
y_val = val_df["Attack_label"].values
val_probs = sup_model.predict_proba(X_val)[:, 1]

# Load autoencoder PyTorch weights to score validation data
device = torch.device("cpu")
ae_net = PyTorchAutoencoder(input_dim=X_val.shape[1])
ae_net.load_state_dict(torch.load(os.path.join(MODELS_DIR, "autoencoder.pt"), map_location=device))
ae_net.eval()

with torch.no_grad():
    val_tensor = torch.tensor(X_val.values if hasattr(X_val, "values") else X_val, dtype=torch.float32)
    val_recon = ae_net(val_tensor)
    val_recon_errors = torch.mean((val_tensor - val_recon) ** 2, dim=1).numpy()

val_norm_errors = val_recon_errors[y_val == 0]
p80_val = float(np.percentile(val_norm_errors, 80.0))
p90_val = float(np.percentile(val_norm_errors, 90.0))
p95_val = float(np.percentile(val_norm_errors, 95.0))
p98_val = float(np.percentile(val_norm_errors, 98.0))
p99_val = float(np.percentile(val_norm_errors, 99.0))

print(f"Validation Autoencoder Thresholds: p80={p80_val:.6f}, p90={p90_val:.6f}, p95={p95_val:.6f}, p98={p98_val:.6f}, p99={p99_val:.6f}")
print(f"Saved JSON p95={ae_thresholds['p95.0']:.6f}, diff={abs(p95_val - ae_thresholds['p95.0']):.8f}")

# -------------------------------------------------------------
# TASK 1: Verification of 8 Configurations on 5,224 Test Records
# -------------------------------------------------------------
print("\n" + "=" * 80)
print("TASK 1: Calculating 8 Configurations on 5,224 Test Records")
print("=" * 80)

configs = [
    ("Supervised threshold 0.50", (test_probs >= 0.50).astype(int)),
    ("Supervised threshold 0.125", (test_probs >= 0.125).astype(int)),
    ("Hybrid p99", ((test_probs >= 0.50) | (test_recon_errors > p99_val)).astype(int)),
    ("Hybrid p98", ((test_probs >= 0.50) | (test_recon_errors > p98_val)).astype(int)),
    ("Hybrid p95", ((test_probs >= 0.50) | (test_recon_errors > p95_val)).astype(int)),
    ("Hybrid p90", ((test_probs >= 0.50) | (test_recon_errors > p90_val)).astype(int)),
    ("Hybrid p80", ((test_probs >= 0.50) | (test_recon_errors > p80_val)).astype(int)),
    ("Tuned supervised + Autoencoder p95", ((test_probs >= 0.125) | (test_recon_errors > p95_val)).astype(int)),
]

t1_rows = []
for name, preds in configs:
    m = calculate_binary_metrics(y_test, preds, test_probs)
    t1_rows.append({
        "configuration": name,
        "test_records": len(y_test),
        "tp": m["tp"],
        "tn": m["tn"],
        "fp": m["fp"],
        "fn": m["fn"],
        "attack_recall": m["attack_recall"],
        "fnr": m["fnr"],
        "fpr": m["fpr"],
        "precision": m["precision"],
        "f1": m["f1"],
        "macro_f1": m["macro_f1"]
    })

t1_df = pd.DataFrame(t1_rows)
t1_path = os.path.join(METRICS_DIR, "confusion_matrix_verification.csv")
t1_df.to_csv(t1_path, index=False)
print(f"Saved Task 1 verification to {t1_path}")
print(t1_df[["configuration", "tp", "tn", "fp", "fn", "attack_recall", "fnr", "fpr", "precision", "f1", "macro_f1"]].to_string())


# -------------------------------------------------------------
# TASK 2: Fair Comparison at FPR <= 5% Constraint
# -------------------------------------------------------------
print("\n" + "=" * 80)
print("TASK 2: Fair Comparison under FPR <= 5% Constraint (Validation-Tuned)")
print("=" * 80)

# 1. Supervised alone: sweep thresholds to find threshold with Val FPR <= 0.05 that maximizes Val Recall
prob_thresholds = np.linspace(0.01, 0.99, 500)
best_sup_thresh = 0.50
best_sup_val_recall = -1.0
best_sup_val_fpr = 1.0

for t in prob_thresholds:
    val_pred = (val_probs >= t).astype(int)
    vm = calculate_binary_metrics(y_val, val_pred)
    if vm["fpr"] <= 0.05:
        if vm["attack_recall"] > best_sup_val_recall or (vm["attack_recall"] == best_sup_val_recall and t > best_sup_thresh):
            best_sup_val_recall = vm["attack_recall"]
            best_sup_val_fpr = vm["fpr"]
            best_sup_thresh = t

print(f"Optimal Supervised threshold on Validation (FPR <= 0.05): t={best_sup_thresh:.4f}, Val FPR={best_sup_val_fpr:.4%}, Val Recall={best_sup_val_recall:.4%}")

# Evaluate Supervised-only on Test
sup_opt_test_preds = (test_probs >= best_sup_thresh).astype(int)
sup_opt_test_m = calculate_binary_metrics(y_test, sup_opt_test_preds, test_probs)

# 2. Hybrid model: select (t_prob, t_ae) on Validation data subject to Val FPR <= 0.05
# Consider standard AE operating points (e.g. p99, p98, p95, p90) and search for t_prob
hybrid_candidates = []
for p_ae, t_ae in [("p99", p99_val), ("p98", p98_val), ("p95", p95_val), ("p90", p90_val)]:
    for t_prob in prob_thresholds:
        hyb_val_pred = ((val_probs >= t_prob) | (val_recon_errors > t_ae)).astype(int)
        vm = calculate_binary_metrics(y_val, hyb_val_pred)
        if vm["fpr"] <= 0.05:
            hybrid_candidates.append({
                "p_ae": p_ae,
                "t_ae": t_ae,
                "t_prob": t_prob,
                "val_recall": vm["attack_recall"],
                "val_fpr": vm["fpr"],
                "val_f1": vm["f1"]
            })

hyb_cand_df = pd.DataFrame(hybrid_candidates)
if not hyb_cand_df.empty:
    # Sort by val_recall descending, then val_f1 descending
    hyb_cand_df = hyb_cand_df.sort_values(by=["val_recall", "val_fpr"], ascending=[False, True])
    best_hyb = hyb_cand_df.iloc[0]
    print(f"Optimal Hybrid on Validation (FPR <= 0.05): AE={best_hyb['p_ae']} (thresh={best_hyb['t_ae']:.6f}), t_prob={best_hyb['t_prob']:.4f}, Val FPR={best_hyb['val_fpr']:.4%}, Val Recall={best_hyb['val_recall']:.4%}")
else:
    print("Warning: No hybrid candidate met Val FPR <= 0.05!")
    best_hyb = {"p_ae": "p99", "t_ae": p99_val, "t_prob": 0.50, "val_recall": 0.0, "val_fpr": 1.0}

# Evaluate Best Hybrid on Test
hyb_opt_test_preds = ((test_probs >= best_hyb["t_prob"]) | (test_recon_errors > best_hyb["t_ae"])).astype(int)
hyb_opt_test_m = calculate_binary_metrics(y_test, hyb_opt_test_preds, test_probs)

# Also test the default baseline hybrid (Supervised 0.50 + AE p98) which has Val FPR <= 0.05
hyb_baseline_val_preds = ((val_probs >= 0.50) | (val_recon_errors > p98_val)).astype(int)
hyb_base_val_m = calculate_binary_metrics(y_val, hyb_baseline_val_preds)
hyb_base_test_preds = ((test_probs >= 0.50) | (test_recon_errors > p98_val)).astype(int)
hyb_base_test_m = calculate_binary_metrics(y_test, hyb_base_test_preds, test_probs)

# Calculate recovered attacks and additional false alarms relative to baseline supervised (0.50) and optimal supervised
sup_050_test_preds = (test_probs >= 0.50).astype(int)
sup_050_m = calculate_binary_metrics(y_test, sup_050_test_preds, test_probs)

# Compute recovered attacks and additional false alarms
# Relative to Supervised Optimal:
hyb_recovered_vs_sup_opt = int(((y_test == 1) & (sup_opt_test_preds == 0) & (hyb_opt_test_preds == 1)).sum())
hyb_extra_fp_vs_sup_opt = int(hyb_opt_test_m["fp"] - sup_opt_test_m["fp"])

# Also for Baseline Hybrid (0.50 + p98) vs Supervised (0.50):
hyb_base_recovered = int(((y_test == 1) & (sup_050_test_preds == 0) & (hyb_base_test_preds == 1)).sum())
hyb_base_extra_fp = int(hyb_base_test_m["fp"] - sup_050_m["fp"])

t2_rows = [
    {
        "model_configuration": f"Supervised-Only (Validation-Tuned t={best_sup_thresh:.3f})",
        "validation_fpr": best_sup_val_fpr,
        "test_fpr": sup_opt_test_m["fpr"],
        "test_attack_recall": sup_opt_test_m["attack_recall"],
        "test_fnr": sup_opt_test_m["fnr"],
        "test_precision": sup_opt_test_m["precision"],
        "test_f1": sup_opt_test_m["f1"],
        "attacks_recovered": 0,
        "additional_false_alarms": 0,
        "tp": sup_opt_test_m["tp"],
        "tn": sup_opt_test_m["tn"],
        "fp": sup_opt_test_m["fp"],
        "fn": sup_opt_test_m["fn"]
    },
    {
        "model_configuration": f"Hybrid Model (Validation-Tuned t_prob={best_hyb['t_prob']:.3f} + AE {best_hyb['p_ae']})",
        "validation_fpr": best_hyb["val_fpr"],
        "test_fpr": hyb_opt_test_m["fpr"],
        "test_attack_recall": hyb_opt_test_m["attack_recall"],
        "test_fnr": hyb_opt_test_m["fnr"],
        "test_precision": hyb_opt_test_m["precision"],
        "test_f1": hyb_opt_test_m["f1"],
        "attacks_recovered": hyb_recovered_vs_sup_opt,
        "additional_false_alarms": hyb_extra_fp_vs_sup_opt,
        "tp": hyb_opt_test_m["tp"],
        "tn": hyb_opt_test_m["tn"],
        "fp": hyb_opt_test_m["fp"],
        "fn": hyb_opt_test_m["fn"]
    },
    {
        "model_configuration": f"Hybrid Baseline (t_prob=0.50 + AE p98)",
        "validation_fpr": hyb_base_val_m["fpr"],
        "test_fpr": hyb_base_test_m["fpr"],
        "test_attack_recall": hyb_base_test_m["attack_recall"],
        "test_fnr": hyb_base_test_m["fnr"],
        "test_precision": hyb_base_test_m["precision"],
        "test_f1": hyb_base_test_m["f1"],
        "attacks_recovered": hyb_base_recovered,
        "additional_false_alarms": hyb_base_extra_fp,
        "tp": hyb_base_test_m["tp"],
        "tn": hyb_base_test_m["tn"],
        "fp": hyb_base_test_m["fp"],
        "fn": hyb_base_test_m["fn"]
    }
]

t2_df = pd.DataFrame(t2_rows)
t2_path = os.path.join(METRICS_DIR, "fpr_constrained_comparison.csv")
t2_df.to_csv(t2_path, index=False)
print(f"Saved Task 2 comparison to {t2_path}")
print(t2_df.to_string())


# -------------------------------------------------------------
# TASK 3: Record-Level Evidence for Supervised False Negatives
# -------------------------------------------------------------
print("\n" + "=" * 80)
print("TASK 3: Record-Level Analysis of Supervised False Negatives & Autoencoder Action")
print("=" * 80)

# Filter all supervised false negatives at t=0.50
sup_fn_indices = np.where((y_test == 1) & (sup_050_test_preds == 0))[0]
print(f"Total Supervised False Negatives (t=0.50): {len(sup_fn_indices)}")

fn_records_list = []
for idx in sup_fn_indices:
    row = test_stream.iloc[idx]
    y_true = int(y_test[idx])
    atk_type = str(row["Attack_type"])
    p_attack = float(test_probs[idx])
    sup_pred = int(sup_050_test_preds[idx])
    recon_err = float(test_recon_errors[idx])
    ae_thresh = p95_val
    ae_anom = int(recon_err > ae_thresh)
    hyb_pred = int((sup_pred == 1) or (ae_anom == 1))
    
    status = "RECOVERED BY AUTOENCODER" if (sup_pred == 0 and hyb_pred == 1) else "REMAINS MISSED (FN)"
    
    fn_records_list.append({
        "record_index": int(idx),
        "ground_truth_label": y_true,
        "attack_type": atk_type,
        "supervised_attack_probability": round(p_attack, 6),
        "supervised_prediction": sup_pred,
        "autoencoder_reconstruction_error": round(recon_err, 6),
        "selected_autoencoder_threshold_p95": round(ae_thresh, 6),
        "autoencoder_anomaly_prediction": ae_anom,
        "final_hybrid_prediction": hyb_pred,
        "resolution_status": status
    })

# Also include normal records that became false alarms under Autoencoder p95
norm_fa_indices = np.where((y_test == 0) & (sup_050_test_preds == 0) & (test_recon_errors > p95_val))[0]
print(f"Total Normal Records turned into False Alarms by Autoencoder (p95): {len(norm_fa_indices)}")

fa_records_list = []
for idx in norm_fa_indices:
    row = test_stream.iloc[idx]
    y_true = int(y_test[idx])
    atk_type = str(row["Attack_type"])
    p_attack = float(test_probs[idx])
    sup_pred = int(sup_050_test_preds[idx])
    recon_err = float(test_recon_errors[idx])
    ae_thresh = p95_val
    ae_anom = int(recon_err > ae_thresh)
    hyb_pred = int((sup_pred == 1) or (ae_anom == 1))
    
    fa_records_list.append({
        "record_index": int(idx),
        "ground_truth_label": y_true,
        "attack_type": atk_type,
        "supervised_attack_probability": round(p_attack, 6),
        "supervised_prediction": sup_pred,
        "autoencoder_reconstruction_error": round(recon_err, 6),
        "selected_autoencoder_threshold_p95": round(ae_thresh, 6),
        "autoencoder_anomaly_prediction": ae_anom,
        "final_hybrid_prediction": hyb_pred,
        "resolution_status": "NEW FALSE ALARM (FP INTRODUCED BY AE)"
    })

all_records = fn_records_list + fa_records_list
t3_df = pd.DataFrame(all_records)
t3_path = os.path.join(METRICS_DIR, "false_negative_record_analysis.csv")
t3_df.to_csv(t3_path, index=False)
print(f"Saved Task 3 record-level analysis ({len(t3_df)} records: {len(fn_records_list)} FNs + {len(fa_records_list)} new FPs) to {t3_path}")
print(t3_df.head(20).to_string())

print("\nAll data generation and verification completed successfully!")

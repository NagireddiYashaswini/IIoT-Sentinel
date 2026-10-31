"""
IIoT SENTINEL 4.0 - Unseen / Zero-Day Attack Detection Experiment
Evaluates model response when selected attack classes are completely held out from supervised training.
"""

import os
import sys
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.preprocessing import IIoTPreprocessor, prepare_and_split_data
from src.data_loader import load_dataset
from src.autoencoder import AutoencoderAnomalyDetector
from utils import calculate_binary_metrics, save_json
import config

print("=" * 80)
print("  UNSEEN ATTACK EXPERIMENT: Completely Excluding Attack Types from Supervised Training")
print("=" * 80)

# Load dataset
df = load_dataset(mode="fast", sample_size=35000, random_seed=42)
train_df, val_df, test_df = prepare_and_split_data(df, seed=42)

# Select 2 attack classes to completely withhold from supervised training
HELD_OUT_ATTACKS = ["Fingerprinting", "MITM"]
print(f"Completely holding out attack classes from supervised training: {HELD_OUT_ATTACKS}")

# 1. Standardized Preprocessor
class StandardizedPreprocessor(IIoTPreprocessor):
    def fit(self, X, y=None):
        X_clean = self._clean_dataframe(X)
        cols_to_remove = set(config.COLUMNS_TO_DROP + config.CONSTANT_COLUMNS + config.TARGET_COLUMNS)
        available_cols = [c for c in X_clean.columns if c not in cols_to_remove]
        self.num_cols = [c for c in available_cols if c in config.NUMERICAL_COLUMNS or c not in config.CATEGORICAL_COLUMNS]
        self.cat_cols = [c for c in available_cols if c in config.CATEGORICAL_COLUMNS]
        
        self.num_imputer = SimpleImputer(strategy="median")
        X_num_imp = self.num_imputer.fit_transform(X_clean[self.num_cols])
        self.scaler = StandardScaler()
        self.scaler.fit(X_num_imp)
        
        self.cat_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.cat_encoder.fit(X_clean[self.cat_cols])
        self.feature_names_out_ = self.num_cols + self.cat_encoder.get_feature_names_out(self.cat_cols).tolist()
        self.is_fitted = True
        return self

# Filter supervised training set FIRST: completely remove held-out attacks prior to preprocessor fitting
train_df_filtered = train_df[~train_df["Attack_type"].isin(HELD_OUT_ATTACKS)].copy()
print(f"Supervised Training Samples: {len(train_df_filtered)} (Removed {len(train_df) - len(train_df_filtered)} records belonging to {HELD_OUT_ATTACKS})")

prep = StandardizedPreprocessor()
prep.fit(train_df_filtered)
X_train_sup = prep.transform(train_df_filtered)
y_train_sup = train_df_filtered["Attack_label"].values

X_val = prep.transform(val_df)
X_test = prep.transform(test_df)

# Train Supervised XGBoost on remaining data
sup_model = xgb.XGBClassifier(n_estimators=100, max_depth=8, learning_rate=0.1, eval_metric="logloss", random_state=42, n_jobs=-1)
sup_model.fit(X_train_sup, y_train_sup)

# Train Autoencoder ONLY on Normal training traffic
norm_train = X_train_sup[train_df_filtered["Attack_label"] == 0]
norm_val = X_val[val_df["Attack_label"] == 0]
ae = AutoencoderAnomalyDetector(input_dim=X_train_sup.shape[1], epochs=15, batch_size=64, random_seed=42)
ae.fit(norm_train, norm_val)

ae_thresh_p95 = ae.thresholds["p95.0"]
ae_thresh_p90 = ae.thresholds["p90.0"]
print(f"Autoencoder validation thresholds: p90={ae_thresh_p90:.4f}, p95={ae_thresh_p95:.4f}")

# Evaluate on Held-Out Attack Records from Test Set
test_held_out_mask = test_df["Attack_type"].isin(HELD_OUT_ATTACKS)
X_test_held = X_test[test_held_out_mask]
y_test_held = test_df.loc[test_held_out_mask, "Attack_type"].values
print(f"\nEvaluating on {len(X_test_held)} held-out test attack records: {dict(pd.Series(y_test_held).value_counts())}")

# Predictions on held-out attacks
sup_held_probs = sup_model.predict_proba(X_test_held)[:, 1]
sup_held_preds = (sup_held_probs >= 0.50).astype(int)
ae_held_errors = ae.calculate_reconstruction_errors(X_test_held)
ae_held_anoms = (ae_held_errors > ae_thresh_p95).astype(int)

# Breakdown per held-out attack
for atk_name in HELD_OUT_ATTACKS:
    atk_mask = (y_test_held == atk_name)
    n_atk = np.sum(atk_mask)
    if n_atk == 0:
        continue
    sup_caught = int(np.sum(sup_held_preds[atk_mask] == 1))
    sup_missed = int(np.sum(sup_held_preds[atk_mask] == 0))
    ae_caught = int(np.sum(ae_held_anoms[atk_mask] == 1))
    
    # Hybrid: caught if supervised caught OR Autoencoder flagged anomaly
    hyb_caught = int(np.sum((sup_held_preds[atk_mask] == 1) | (ae_held_anoms[atk_mask] == 1)))
    potential_unknown = int(np.sum((sup_held_preds[atk_mask] == 0) & (ae_held_anoms[atk_mask] == 1)))
    
    print(f"\nAttack Vector: {atk_name} (Total: {n_atk})")
    print(f"  Supervised Model (Never trained on {atk_name}):")
    print(f"    - Detected (generalized via similar traffic): {sup_caught} ({sup_caught/n_atk*100:.1f}%)")
    print(f"    - Missed (False Negatives): {sup_missed} ({sup_missed/n_atk*100:.1f}%)")
    print(f"  Autoencoder (Trained only on Normal):")
    print(f"    - Flagged as Anomaly: {ae_caught} ({ae_caught/n_atk*100:.1f}%)")
    print(f"  Hybrid System:")
    print(f"    - Total Caught: {hyb_caught} ({hyb_caught/n_atk*100:.1f}%)")
    print(f"    - Specifically Caught as 'POTENTIAL UNKNOWN ATTACK': {potential_unknown} ({potential_unknown/n_atk*100:.1f}%)")

print("\n" + "=" * 80)
print("Experiment completed successfully.")


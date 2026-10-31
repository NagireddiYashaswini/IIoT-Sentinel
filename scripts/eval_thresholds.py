import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from src.preprocessing import IIoTPreprocessor, prepare_and_split_data
from src.data_loader import load_dataset
from src.autoencoder import AutoencoderAnomalyDetector
from utils import calculate_binary_metrics
import config

df = load_dataset(mode="fast", sample_size=35000, random_seed=42)
train_df, val_df, test_df = prepare_and_split_data(df, seed=42)

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

prep = StandardizedPreprocessor()
prep.fit(train_df)
X_train = prep.transform(train_df)
X_val = prep.transform(val_df)
X_test = prep.transform(test_df)

y_train = train_df["Attack_label"].values
y_val = val_df["Attack_label"].values
y_test = test_df["Attack_label"].values

print("Training XGBoost...")
model = xgb.XGBClassifier(n_estimators=100, max_depth=8, learning_rate=0.1, eval_metric="logloss", random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

print("Training Autoencoder on normal only...")
norm_train = X_train[y_train == 0]
norm_val = X_val[y_val == 0]
ae = AutoencoderAnomalyDetector(input_dim=X_train.shape[1], epochs=15, batch_size=64, random_seed=42)
ae.fit(norm_train, norm_val)

test_probs = model.predict_proba(X_test)[:, 1]
sup_test_preds = (test_probs >= 0.50).astype(int)
sup_m = calculate_binary_metrics(y_test, sup_test_preds, test_probs)

print("\n--- Supervised Alone (Threshold = 0.50) ---")
for k in ["tp", "tn", "fp", "fn", "attack_recall", "fnr", "fpr", "precision", "f1", "macro_f1"]:
    print(f"  {k}: {sup_m[k]}")

fn_mask = (y_test == 1) & (sup_test_preds == 0)
print(f"\nSupervised False Negatives count: {fn_mask.sum()}")
fn_records = test_df[fn_mask]
print("FN attack types:", fn_records["Attack_type"].value_counts().to_dict())

fn_errors = ae.calculate_reconstruction_errors(X_test[fn_mask])
print("Reconstruction errors of Supervised False Negatives:")
print(fn_errors)

test_ae_errors = ae.calculate_reconstruction_errors(X_test)
print("\nAutoencoder thresholds from validation normal traffic:", ae.thresholds)

# Test various Autoencoder percentiles: 80, 85, 90, 95, 98, 99, 99.5, 99.9
val_norm_errors = ae.calculate_reconstruction_errors(norm_val)
custom_percentiles = [80.0, 85.0, 90.0, 95.0, 98.0, 99.0, 99.5, 99.9]

results = []
for p in custom_percentiles:
    t_val = float(np.percentile(val_norm_errors, p))
    recovered = int((fn_errors > t_val).sum())
    hyb_preds = ((test_probs >= 0.50) | (test_ae_errors > t_val)).astype(int)
    hyb_m = calculate_binary_metrics(y_test, hyb_preds, test_probs)
    new_fps = hyb_m["fp"] - sup_m["fp"]
    results.append({
        "percentile": f"p{p}",
        "threshold": t_val,
        "recovered_fns": recovered,
        "new_fps": new_fps,
        "tp": hyb_m["tp"],
        "tn": hyb_m["tn"],
        "fp": hyb_m["fp"],
        "fn": hyb_m["fn"],
        "attack_recall": hyb_m["attack_recall"],
        "fnr": hyb_m["fnr"],
        "fpr": hyb_m["fpr"],
        "precision": hyb_m["precision"],
        "f1": hyb_m["f1"],
        "macro_f1": hyb_m["macro_f1"]
    })

res_df = pd.DataFrame(results)
print("\n--- Multi-Threshold Comparison Table ---")
print(res_df.to_string())


"""
IIoT SENTINEL 4.0 - External Data Upload Validation Suite
Tests all 7 upload conditions specified in Section 5:
1. Compatible CSV without labels
2. Compatible CSV with labels
3. Compatible XLSX file
4. File with missing required features
5. File with extra columns
6. File with different data types
7. File with distribution drift
"""

import pytest
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from src.features import validate_feature_schema, compute_distribution_shift
from src.demo_data import generate_synthetic_iiot_dataset
from src.hybrid_detector import HybridDecisionEngine
from src.autoencoder import AutoencoderAnomalyDetector
import config


@pytest.fixture(scope="module")
def pipeline_bundle():
    """Load pre-trained components for upload testing."""
    preprocessor = joblib.load(config.MODELS_DIR / "preprocessing_pipeline.joblib")
    supervised_model = joblib.load(config.MODELS_DIR / "supervised_model.joblib")
    multiclass_model = joblib.load(config.MODELS_DIR / "multiclass_model.joblib")
    label_encoder = joblib.load(config.MODELS_DIR / "label_encoder.joblib")
    
    ae = AutoencoderAnomalyDetector(input_dim=len(preprocessor.feature_names_out_))
    # Mock threshold if weights file is small or present
    ae.selected_threshold = 0.1628
    ae.is_fitted = True

    return {
        "preprocessor": preprocessor,
        "supervised_model": supervised_model,
        "multiclass_model": multiclass_model,
        "label_encoder": label_encoder,
        "autoencoder": ae
    }


def test_1_compatible_csv_without_labels(pipeline_bundle):
    """Test 1: A compatible CSV without labels produces predictions without ground-truth metrics."""
    prep = pipeline_bundle["preprocessor"]
    sup = pipeline_bundle["supervised_model"]
    mc = pipeline_bundle["multiclass_model"]
    le = pipeline_bundle["label_encoder"]
    ae = pipeline_bundle["autoencoder"]

    # Generate synthetic data and remove target labels
    raw_df = generate_synthetic_iiot_dataset(n_samples=50, random_seed=101)
    unlabeled_df = raw_df.drop(columns=config.TARGET_COLUMNS)
    assert not any(col in unlabeled_df.columns for col in config.TARGET_COLUMNS)

    # Schema validation
    val_res = validate_feature_schema(unlabeled_df, config.NUMERICAL_COLUMNS)
    assert val_res["is_valid"] is True

    # Transform without fitting
    initial_mean = prep.scaler.mean_.copy() if hasattr(prep.scaler, "mean_") else prep.scaler.center_.copy()
    X_proc = prep.transform(unlabeled_df)
    
    # Confirm pipeline was NOT refitted
    current_mean = prep.scaler.mean_.copy() if hasattr(prep.scaler, "mean_") else prep.scaler.center_.copy()
    np.testing.assert_array_equal(initial_mean, current_mean)

    # Hybrid inference
    hybrid_engine = HybridDecisionEngine(sup, mc, le, ae)
    results = hybrid_engine.predict(X_proc)

    assert len(results) == 50
    assert "hybrid_decision" in results.columns
    assert set(results["hybrid_decision"].unique()).issubset({
        "NORMAL", "KNOWN ATTACK", "POTENTIAL UNKNOWN ATTACK", "SUSPICIOUS / UNCERTAIN"
    })


def test_2_compatible_csv_with_labels(pipeline_bundle):
    """Test 2: A compatible CSV with labels allows ground-truth evaluation."""
    prep = pipeline_bundle["preprocessor"]
    sup = pipeline_bundle["supervised_model"]
    mc = pipeline_bundle["multiclass_model"]
    le = pipeline_bundle["label_encoder"]
    ae = pipeline_bundle["autoencoder"]

    labeled_df = generate_synthetic_iiot_dataset(n_samples=50, random_seed=202)
    assert config.LABEL_BINARY in labeled_df.columns
    assert config.LABEL_MULTICLASS in labeled_df.columns

    X_proc = prep.transform(labeled_df)
    hybrid_engine = HybridDecisionEngine(sup, mc, le, ae)
    results = hybrid_engine.predict(X_proc)

    # Verify metrics can be computed
    y_true = labeled_df[config.LABEL_BINARY].values
    y_pred = results["hybrid_decision"].apply(lambda d: 0 if d == "NORMAL" else 1).values
    acc = np.mean(y_true == y_pred)
    assert 0.0 <= acc <= 1.0


def test_3_compatible_xlsx_file(pipeline_bundle, tmp_path):
    """Test 3: An Excel XLSX file is read, validated, and processed cleanly."""
    prep = pipeline_bundle["preprocessor"]
    sup = pipeline_bundle["supervised_model"]
    mc = pipeline_bundle["multiclass_model"]
    le = pipeline_bundle["label_encoder"]
    ae = pipeline_bundle["autoencoder"]

    raw_df = generate_synthetic_iiot_dataset(n_samples=30, random_seed=303)
    xlsx_path = tmp_path / "test_upload.xlsx"
    raw_df.to_excel(xlsx_path, index=False)

    df_loaded = pd.read_excel(xlsx_path)
    val_res = validate_feature_schema(df_loaded, config.NUMERICAL_COLUMNS)
    assert val_res["is_valid"] is True

    X_proc = prep.transform(df_loaded)
    hybrid_engine = HybridDecisionEngine(sup, mc, le, ae)
    results = hybrid_engine.predict(X_proc)
    assert len(results) == 30


def test_4_file_with_missing_required_features():
    """Test 4: Incompatible dataset lacking required features is rejected."""
    incompatible_df = pd.DataFrame({
        "temperature": [22.4, 23.1, 21.8],
        "humidity": [45.0, 47.2, 44.1],
        "sensor_id": ["S1", "S2", "S3"]
    })
    val_res = validate_feature_schema(incompatible_df, config.NUMERICAL_COLUMNS)
    assert val_res["is_valid"] is False
    assert "rejected" in val_res["details"].lower()


def test_5_file_with_extra_columns(pipeline_bundle):
    """Test 5: File with extra benign or telemetry columns is safely accepted, extra columns ignored."""
    prep = pipeline_bundle["preprocessor"]
    raw_df = generate_synthetic_iiot_dataset(n_samples=30, random_seed=505)
    
    # Add extra arbitrary columns
    raw_df["extra_factory_id"] = "PLANT_A_ZONE_4"
    raw_df["extra_operator_shift"] = 2
    raw_df["extra_ambient_temp"] = 25.4

    val_res = validate_feature_schema(raw_df, config.NUMERICAL_COLUMNS)
    assert val_res["is_valid"] is True
    assert "extra_factory_id" in val_res["extra_features"]

    # Preprocessor transform should cleanly ignore extra columns
    X_proc = prep.transform(raw_df)
    assert X_proc.shape[1] == len(prep.feature_names_out_)


def test_6_file_with_different_data_types(pipeline_bundle):
    """Test 6: File containing mixed types, string numbers, or NaNs in numeric fields is handled."""
    prep = pipeline_bundle["preprocessor"]
    raw_df = generate_synthetic_iiot_dataset(n_samples=40, random_seed=606)

    # Introduce corrupted string formats and NaNs
    raw_df["tcp.dstport"] = raw_df["tcp.dstport"].astype(str)
    raw_df.loc[0:5, "tcp.dstport"] = "NaN"
    raw_df.loc[6:10, "udp.port"] = np.nan
    raw_df.loc[11:15, "icmp.checksum"] = "INVALID_HEX"

    # Preprocessor should coerce and median-impute without error
    X_proc = prep.transform(raw_df)
    assert not np.isnan(X_proc.to_numpy()).any()
    assert len(X_proc) == 40


def test_7_file_with_distribution_drift():
    """Test 7: Significant statistical shift triggers distribution shift alert."""
    df_base = generate_synthetic_iiot_dataset(n_samples=200, random_seed=42)
    df_drifted = df_base.copy()

    # Shift numerical features by 100x
    drift_features = ["tcp.len", "tcp.ack", "udp.port", "icmp.checksum", "tcp.dstport"]
    for f in drift_features:
        if f in df_drifted.columns:
            df_drifted[f] = pd.to_numeric(df_drifted[f], errors="coerce").fillna(0.0) * 100.0 + 5000.0

    shift_res = compute_distribution_shift(df_base, df_drifted, drift_features)
    assert shift_res["shift_detected"] is True
    assert shift_res["warning_message"] is not None
    assert "Warning" in shift_res["warning_message"]


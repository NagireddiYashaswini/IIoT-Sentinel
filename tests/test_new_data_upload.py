"""
IIoT SENTINEL 4.0 - New Data Upload & External Testing Tests
Verifies schema validation, incompatible dataset rejection, distribution shift alerts, and offline prediction replay.
"""

import pytest
import numpy as np
import pandas as pd
import joblib
from src.features import validate_feature_schema, compute_distribution_shift
from src.demo_data import generate_synthetic_iiot_dataset
from src.preprocessing import IIoTPreprocessor
import config


def test_schema_validation_compatible():
    """Verify compatible new dataset is accepted."""
    df = generate_synthetic_iiot_dataset(n_samples=50, random_seed=123)
    preprocessor = joblib.load(config.MODELS_DIR / "preprocessing_pipeline.joblib")
    
    validation = validate_feature_schema(df, config.NUMERICAL_COLUMNS)
    assert validation["is_valid"] is True
    assert validation["match_ratio"] >= 0.70


def test_schema_validation_incompatible():
    """Verify completely foreign dataset (e.g. housing or iris data) is rejected."""
    incompatible_df = pd.DataFrame({
        "sepal_length": [5.1, 4.9],
        "sepal_width": [3.5, 3.0],
        "petal_length": [1.4, 1.4],
        "species": ["setosa", "setosa"]
    })
    validation = validate_feature_schema(incompatible_df, config.NUMERICAL_COLUMNS)
    assert validation["is_valid"] is False
    assert "rejected" in validation["details"].lower()


def test_distribution_shift_detection():
    """Verify statistical shift is flagged when features have drastically different distributions."""
    df_base = generate_synthetic_iiot_dataset(n_samples=200, random_seed=42)
    # Create shifted data by multiplying numerical features by 50
    df_shifted = df_base.copy()
    for col in ["tcp.len", "tcp.ack", "udp.port"]:
        if col in df_shifted.columns:
            df_shifted[col] = pd.to_numeric(df_shifted[col], errors="coerce") * 50.0

    shift_result = compute_distribution_shift(df_base, df_shifted, ["tcp.len", "tcp.ack", "udp.port"])
    assert shift_result["shifted_features_count"] > 0


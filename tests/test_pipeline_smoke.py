"""
IIoT SENTINEL 4.0 - Pipeline Smoke Tests
Verifies that all core components instantiate and run without crashing.
"""

import pytest
import numpy as np
import pandas as pd
from src.demo_data import generate_synthetic_iiot_dataset
from src.preprocessing import IIoTPreprocessor, prepare_and_split_data
from src.models import build_binary_classifier, train_multiclass_model
from src.autoencoder import AutoencoderAnomalyDetector
from src.hybrid_detector import HybridDecisionEngine
from src.validate_artifacts import validate_artifacts
import config


def test_synthetic_data_generation():
    df = generate_synthetic_iiot_dataset(n_samples=200, random_seed=42)
    assert len(df) == 200
    assert config.LABEL_BINARY in df.columns
    assert config.LABEL_MULTICLASS in df.columns
    assert df[config.LABEL_BINARY].nunique() == 2


def test_preprocessor_fit_transform():
    df = generate_synthetic_iiot_dataset(n_samples=200, random_seed=42)
    train_df, val_df, test_df = prepare_and_split_data(df, seed=42)

    preprocessor = IIoTPreprocessor()
    preprocessor.fit(train_df)
    
    assert preprocessor.is_fitted
    assert len(preprocessor.feature_names_out_) > 0

    X_train = preprocessor.transform(train_df)
    X_val = preprocessor.transform(val_df)
    X_test = preprocessor.transform(test_df)

    assert X_train.shape[1] == len(preprocessor.feature_names_out_)
    assert X_val.shape[1] == len(preprocessor.feature_names_out_)
    assert X_test.shape[1] == len(preprocessor.feature_names_out_)
    assert not np.isnan(X_train.to_numpy()).any()


def test_artifact_validation_passes():
    status, report = validate_artifacts()
    assert status is True
    assert len(report["missing_files"]) == 0


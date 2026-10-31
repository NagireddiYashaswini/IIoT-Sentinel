"""
IIoT SENTINEL 4.0 - Autoencoder Anomaly Tests
Verifies normal-only Autoencoder convergence, non-negative reconstruction errors, and threshold decision mechanics.
"""

import pytest
import numpy as np
import torch
from src.autoencoder import AutoencoderAnomalyDetector, PyTorchAutoencoder
from src.demo_data import generate_synthetic_iiot_dataset
from src.preprocessing import IIoTPreprocessor, prepare_and_split_data
import config


def test_autoencoder_architecture():
    """Verify PyTorch model input/output dimensionality."""
    input_dim = 40
    model = PyTorchAutoencoder(input_dim=input_dim)
    dummy_x = torch.randn(10, input_dim)
    reconstructed = model(dummy_x)
    assert reconstructed.shape == dummy_x.shape


def test_autoencoder_training_and_thresholding():
    """Verify Autoencoder trains and generates valid percentile thresholds."""
    df = generate_synthetic_iiot_dataset(n_samples=400, random_seed=42)
    train_df, val_df, test_df = prepare_and_split_data(df, seed=42)

    preprocessor = IIoTPreprocessor()
    preprocessor.fit(train_df)

    X_train = preprocessor.transform(train_df)
    X_val = preprocessor.transform(val_df)
    X_test = preprocessor.transform(test_df)

    # Train strictly on normal records
    norm_train = X_train[train_df[config.LABEL_BINARY] == 0]
    norm_val = X_val[val_df[config.LABEL_BINARY] == 0]

    detector = AutoencoderAnomalyDetector(input_dim=X_train.shape[1], epochs=5, batch_size=32, random_seed=42)
    detector.fit(norm_train, norm_val)

    assert detector.is_fitted
    assert detector.selected_threshold is not None
    assert detector.selected_threshold > 0.0

    # Test reconstruction errors
    errors = detector.calculate_reconstruction_errors(X_test)
    assert len(errors) == len(X_test)
    assert (errors >= 0).all()

    # Test anomaly predictions
    anomalies, _ = detector.predict(X_test)
    assert set(np.unique(anomalies)).issubset({0, 1})


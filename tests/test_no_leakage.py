"""
IIoT SENTINEL 4.0 - Data Leakage Prevention Tests
Verifies absence of target leakage, strict partition disjointness, and frozen preprocessor state during inference.
"""

import pytest
import numpy as np
import pandas as pd
from src.demo_data import generate_synthetic_iiot_dataset
from src.preprocessing import IIoTPreprocessor, prepare_and_split_data
import config


def test_no_target_in_features():
    """Verify that target columns are completely removed from input feature representations."""
    df = generate_synthetic_iiot_dataset(n_samples=300, random_seed=42)
    preprocessor = IIoTPreprocessor()
    preprocessor.fit(df)

    for target in config.TARGET_COLUMNS:
        assert target not in preprocessor.feature_names_out_
        assert not any(target in col for col in preprocessor.feature_names_out_)


def test_no_identifier_leakage():
    """Verify that timestamps and static IP addresses are excluded from features."""
    df = generate_synthetic_iiot_dataset(n_samples=300, random_seed=42)
    preprocessor = IIoTPreprocessor()
    preprocessor.fit(df)

    for dropped_col in config.COLUMNS_TO_DROP:
        assert dropped_col not in preprocessor.feature_names_out_


def test_splits_are_mutually_exclusive():
    """Verify that train, validation, and test sets share zero overlapping indices."""
    df = generate_synthetic_iiot_dataset(n_samples=500, random_seed=42)
    train_df, val_df, test_df = prepare_and_split_data(df, seed=42)

    train_idx = set(train_df.index)
    val_idx = set(val_df.index)
    test_idx = set(test_df.index)

    assert len(train_idx.intersection(val_idx)) == 0
    assert len(train_idx.intersection(test_idx)) == 0
    assert len(val_idx.intersection(test_idx)) == 0
    assert len(train_df) + len(val_df) + len(test_df) == len(df)


def test_preprocessor_does_not_refit_on_transform():
    """Verify that scaler parameters do not change when transforming new data."""
    df1 = generate_synthetic_iiot_dataset(n_samples=300, random_seed=42)
    df2 = generate_synthetic_iiot_dataset(n_samples=100, random_seed=999)

    preprocessor = IIoTPreprocessor()
    preprocessor.fit(df1)

    initial_mean = preprocessor.scaler.mean_.copy()
    initial_scale = preprocessor.scaler.scale_.copy()

    # Transform new data
    _ = preprocessor.transform(df2)

    # Scaler means and scales must remain identical
    np.testing.assert_array_equal(preprocessor.scaler.mean_, initial_mean)
    np.testing.assert_array_equal(preprocessor.scaler.scale_, initial_scale)


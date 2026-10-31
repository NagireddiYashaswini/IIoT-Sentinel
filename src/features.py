"""
IIoT SENTINEL 4.0 - Feature Management & Distribution Shift Detection
Handles feature schema validation, distribution comparison, and shift alerts.
"""

import json
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from utils import logger, save_json, load_json
import config


def validate_feature_schema(uploaded_df, expected_features):
    """
    Validate whether an uploaded dataset matches the expected feature schema.
    
    Returns:
    --------
    dict with keys:
        is_valid: bool
        missing_features: list
        extra_features: list
        matched_features: list
        details: str
    """
    uploaded_cols = set(uploaded_df.columns)
    expected_cols = set(expected_features)

    matched = list(expected_cols.intersection(uploaded_cols))
    missing = list(expected_cols - uploaded_cols)
    extra = list(uploaded_cols - expected_cols)

    match_ratio = len(matched) / len(expected_cols) if expected_cols else 1.0
    
    # We consider the dataset valid if at least 70% of numerical/behavioral features match
    is_valid = match_ratio >= 0.70

    if not is_valid:
        details = (
            f"Dataset rejected: Only {len(matched)} of {len(expected_cols)} required features found "
            f"({match_ratio*100:.1f}% match). Missing critical columns: {missing[:5]}..."
        )
    else:
        details = f"Feature schema validated successfully ({len(matched)}/{len(expected_cols)} features matched)."

    return {
        "is_valid": is_valid,
        "match_ratio": match_ratio,
        "matched_features": matched,
        "missing_features": missing,
        "extra_features": extra,
        "details": details
    }


def compute_distribution_shift(baseline_df, new_df, feature_cols, alpha=0.01):
    """
    Test for statistical distribution shift between baseline training data and newly uploaded data
    using the Kolmogorov-Smirnov 2-sample test across numerical features.
    
    Returns:
    --------
    dict with:
        shift_detected: bool
        shifted_features_count: int
        total_features_tested: int
        shifted_feature_names: list
        shift_ratio: float
        warning_message: str or None
    """
    shifted_features = []
    tested_count = 0

    for col in feature_cols:
        if col in baseline_df.columns and col in new_df.columns:
            base_vals = pd.to_numeric(baseline_df[col], errors="coerce").dropna()
            new_vals = pd.to_numeric(new_df[col], errors="coerce").dropna()

            if len(base_vals) > 20 and len(new_vals) > 20:
                tested_count += 1
                try:
                    stat, p_val = ks_2samp(base_vals, new_vals)
                    # If p-value is extremely low, reject null hypothesis (distributions differ)
                    if p_val < alpha:
                        shifted_features.append({"feature": col, "ks_stat": float(stat), "p_value": float(p_val)})
                except Exception:
                    pass

    shift_ratio = len(shifted_features) / tested_count if tested_count > 0 else 0.0
    shift_detected = shift_ratio > 0.40  # If more than 40% of features show significant drift

    warning_message = None
    if shift_detected:
        warning_message = (
            f"Warning: The uploaded dataset exhibits a significant traffic distribution shift "
            f"({len(shifted_features)} of {tested_count} features differed significantly, KS alpha={alpha}). "
            f"Model prediction reliability may be reduced."
        )

    return {
        "shift_detected": shift_detected,
        "shifted_features_count": len(shifted_features),
        "total_features_tested": tested_count,
        "shifted_feature_names": [f["feature"] for f in shifted_features],
        "shift_ratio": float(shift_ratio),
        "warning_message": warning_message
    }


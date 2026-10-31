"""
IIoT SENTINEL 4.0 - Imbalance Handling & False-Negative Reduction
Implements class weighting, training-only SMOTE, and validation-based decision threshold tuning.
"""

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight
from imblearn.over_sampling import SMOTE
from utils import logger, calculate_binary_metrics
import config


def get_class_weights(y_train):
    """Calculate balanced class weights for training to penalize minority misclassifications."""
    classes = np.unique(y_train)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_train)
    weight_dict = {cls: float(w) for cls, w in zip(classes, weights)}
    logger.info(f"Computed class weights: {weight_dict}")
    return weight_dict


def apply_smote_train_only(X_train, y_train, random_seed=config.RANDOM_SEED):
    """
    Apply SMOTE exclusively to the training split to synthesize minority samples.
    NEVER apply to validation or test data!
    """
    logger.info(f"Applying SMOTE to training set only (initial shape: {X_train.shape}, classes: {np.bincount(y_train)})...")
    # Identify k_neighbors based on minority count
    min_count = np.min(np.bincount(y_train))
    k_neighbors = min(5, max(1, min_count - 1))
    
    smote = SMOTE(k_neighbors=k_neighbors, random_state=random_seed)
    X_res, y_res = smote.fit_resample(X_train, y_train)
    logger.info(f"SMOTE complete. Resampled shape: {X_res.shape}, classes: {np.bincount(y_res)}")
    return X_res, y_res


def optimize_decision_threshold(y_val, y_val_probs, max_fpr=0.05):
    """
    Tune binary decision threshold strictly on the VALIDATION split.
    Sweeps thresholds from 0.05 to 0.95 to find the threshold that directly
    minimizes False Negatives (maximizes Attack Recall) while keeping FPR constrained.
    
    Returns:
    --------
    dict with:
        best_threshold: float
        default_metrics (at 0.50): dict
        optimized_metrics (at best_threshold): dict
        threshold_curve: list of dicts for plotting
    """
    logger.info("Executing validation-based threshold optimization for False-Negative reduction...")
    thresholds = np.linspace(0.05, 0.95, 37)
    curve = []
    
    default_metrics = None
    best_threshold = 0.50
    best_score = -1.0
    
    for t in thresholds:
        preds = (y_val_probs >= t).astype(int)
        metrics = calculate_binary_metrics(y_val, preds, y_val_probs)
        metrics["threshold"] = float(np.round(t, 3))
        curve.append(metrics)
        
        if np.isclose(t, 0.50):
            default_metrics = metrics

        # Optimization objective: Maximize Attack Recall (1 - FNR)
        # Apply heavy penalty if FPR exceeds operational ceiling (max_fpr)
        score = metrics["attack_recall"]
        if metrics["fpr"] > max_fpr:
            score -= (metrics["fpr"] - max_fpr) * 3.0
            
        if score > best_score:
            best_score = score
            best_threshold = float(np.round(t, 3))

    if default_metrics is None:
        preds = (y_val_probs >= 0.5).astype(int)
        default_metrics = calculate_binary_metrics(y_val, preds, y_val_probs)
        default_metrics["threshold"] = 0.5

    # Compute metrics at selected best threshold
    opt_preds = (y_val_probs >= best_threshold).astype(int)
    optimized_metrics = calculate_binary_metrics(y_val, opt_preds, y_val_probs)
    optimized_metrics["threshold"] = best_threshold

    logger.info(
        f"Threshold optimization result: Default 0.50 -> Optimized {best_threshold:.3f}. "
        f"FNR: {default_metrics['fnr']*100:.2f}% -> {optimized_metrics['fnr']*100:.2f}%. "
        f"Attack Recall: {default_metrics['attack_recall']*100:.2f}% -> {optimized_metrics['attack_recall']*100:.2f}%."
    )

    return {
        "best_threshold": best_threshold,
        "default_metrics": default_metrics,
        "optimized_metrics": optimized_metrics,
        "threshold_curve": curve
    }


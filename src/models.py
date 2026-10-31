"""
IIoT SENTINEL 4.0 - Supervised Machine Learning Models
Implements binary (Normal vs Attack) and multiclass (15 classes) classifiers with cross-model benchmarking.
"""

import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

from utils import logger, calculate_binary_metrics, Timer
import config


def build_binary_classifier(model_name="rf", random_seed=config.RANDOM_SEED, class_weight="balanced"):
    """Instantiate a supervised binary classification model by identifier."""
    if model_name == "rf":
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=16,
            min_samples_split=5,
            class_weight=class_weight,
            random_state=random_seed,
            n_jobs=-1
        )
    elif model_name == "dt":
        return DecisionTreeClassifier(
            max_depth=14,
            min_samples_split=5,
            class_weight=class_weight,
            random_state=random_seed
        )
    elif model_name == "lr":
        return LogisticRegression(
            max_iter=1000,
            class_weight=class_weight,
            random_state=random_seed,
            solver="lbfgs"
        )
    elif model_name == "xgb":
        return xgb.XGBClassifier(
            n_estimators=100,
            max_depth=8,
            learning_rate=0.1,
            eval_metric="logloss",
            random_state=random_seed,
            n_jobs=-1
        )
    else:
        raise ValueError(f"Unsupported model identifier: {model_name}. Supported: ['rf', 'dt', 'lr', 'xgb']")


def train_and_evaluate_binary_models(X_train, y_train, X_val, y_val, model_names=None, random_seed=config.RANDOM_SEED):
    """
    Train and benchmark candidate binary models on validation split.
    Selects the best model according to Validation Macro F1 and Attack Recall.
    
    Returns:
    --------
    best_model, best_name, benchmark_results (dict of metrics and timings)
    """
    if model_names is None:
        model_names = config.DEFAULT_MODELS

    logger.info(f"Training and comparing binary classifiers: {model_names}...")
    benchmarks = {}
    best_name = None
    best_model = None
    best_score = -1.0

    for name in model_names:
        logger.info(f"--- Training candidate model: {name.upper()} ---")
        model = build_binary_classifier(name, random_seed=random_seed)

        # Measure training time
        t_start = time.perf_counter()
        model.fit(X_train, y_train)
        t_train = time.perf_counter() - t_start

        # Measure inference latency on validation set
        t_inf_start = time.perf_counter()
        val_preds = model.predict(X_val)
        t_inference = time.perf_counter() - t_inf_start
        val_latency_ms = (t_inference / len(X_val)) * 1000.0  # ms per sample

        # Probability outputs for threshold tuning & ROC
        if hasattr(model, "predict_proba"):
            val_probs = model.predict_proba(X_val)[:, 1]
        else:
            val_probs = val_preds.astype(float)

        metrics = calculate_binary_metrics(y_val, val_preds, val_probs)
        metrics["model_name"] = name.upper()
        metrics["train_time_sec"] = float(np.round(t_train, 3))
        metrics["inference_latency_ms_per_sample"] = float(np.round(val_latency_ms, 4))

        benchmarks[name] = {
            "metrics": metrics,
            "model": model,
            "val_probs": val_probs
        }

        logger.info(
            f"[{name.upper()}] Accuracy: {metrics['accuracy']*100:.2f}%, "
            f"Attack Recall: {metrics['attack_recall']*100:.2f}%, "
            f"FNR: {metrics['fnr']*100:.2f}%, "
            f"Macro F1: {metrics['macro_f1']*100:.2f}%, "
            f"Latency: {val_latency_ms:.4f} ms/sample"
        )

        # Selection criterion: Validation Macro F1 + Attack Recall
        score = metrics["macro_f1"] * 0.6 + metrics["attack_recall"] * 0.4
        if score > best_score:
            best_score = score
            best_name = name
            best_model = model

    logger.info(f"Selected best binary model: {best_name.upper()} (Score: {best_score:.4f})")
    return best_model, best_name, benchmarks


def train_multiclass_model(X_train, y_train_multiclass, X_val, y_val_multiclass, random_seed=config.RANDOM_SEED):
    """
    Train multiclass attack classifier to categorize specific attack types.
    Uses actual dataset classes without inventing classes.
    """
    logger.info("Training Multiclass Attack Classifier (Random Forest)...")
    
    # Fit LabelEncoder for string attack classes
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train_multiclass)
    y_val_encoded = le.transform(y_val_multiclass)
    class_names = [str(c) for c in le.classes_]

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=16,
        min_samples_split=5,
        class_weight="balanced",
        random_state=random_seed,
        n_jobs=-1
    )

    with Timer("Multiclass Model Training"):
        model.fit(X_train, y_train_encoded)

    # Evaluate on validation split
    val_preds = model.predict(X_val)
    val_probs = model.predict_proba(X_val)
    
    report = classification_report(
        y_val_encoded,
        val_preds,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )
    cm = confusion_matrix(y_val_encoded, val_preds).tolist()

    logger.info("Multiclass Attack Classifier training and validation complete.")
    return model, le, class_names, report, cm


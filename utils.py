"""
IIoT SENTINEL 4.0 - Utilities Module
Common logging, metrics calculation, JSON serialization, and helper functions.
"""

import os
import json
import time
import logging
import tempfile
import numpy as np
from datetime import datetime

# Prevent Matplotlib cache permission warnings on Windows
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("IIoT-Sentinel")


class NpEncoder(json.JSONEncoder):
    """Custom JSON encoder to safely serialize NumPy types, float NaNs, and Infs."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            if np.isnan(obj) or np.isneginf(obj) or np.isposinf(obj):
                return None
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return super(NpEncoder, self).default(obj)


def sanitize_dict_for_json(data):
    """Recursively sanitize dictionary values to guarantee valid JSON without NaN or Inf."""
    if isinstance(data, dict):
        return {str(k): sanitize_dict_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict_for_json(item) for item in data]
    elif isinstance(data, (float, np.floating)):
        if np.isnan(data) or np.isneginf(data) or np.isposinf(data):
            return 0.0
        return float(data)
    elif isinstance(data, (int, np.integer)):
        return int(data)
    elif isinstance(data, (bool, np.bool_)):
        return bool(data)
    return data


def save_json(data, filepath):
    """Safely save a dictionary to a JSON file."""
    sanitized = sanitize_dict_for_json(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, indent=2, cls=NpEncoder)


def load_json(filepath):
    """Load JSON file safely."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_binary_metrics(y_true, y_pred, y_prob=None):
    """
    Compute binary classification performance metrics focusing on False-Negative reduction.
    Class 0 = Normal, Class 1 = Attack.
    TP: True Positives (Attack correctly detected)
    FP: False Positives (Normal falsely flagged as Attack)
    TN: True Negatives (Normal correctly identified)
    FN: False Negatives (Attack falsely classified as Normal - CRITICAL)
    """
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, roc_auc_score
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    # Structure of confusion matrix with labels [0, 1]:
    # [[TN, FP],
    #  [FN, TP]]
    tn, fp, fn, tp = cm.ravel()

    total_attacks = int(tp + fn)
    total_normals = int(tn + fp)

    # Attack Recall = TP / (TP + FN)
    attack_recall = float(tp / total_attacks) if total_attacks > 0 else 0.0
    # False Negative Rate = FN / (TP + FN)
    fnr = float(fn / total_attacks) if total_attacks > 0 else 0.0
    # False Positive Rate = FP / (FP + TN)
    fpr = float(fp / total_normals) if total_normals > 0 else 0.0
    # Precision = TP / (TP + FP)
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0

    acc = float(accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    auc = None
    if y_prob is not None:
        try:
            auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            auc = 0.5

    return {
        "accuracy": acc,
        "precision": precision,
        "recall": attack_recall,
        "attack_recall": attack_recall,
        "f1": f1,
        "macro_f1": macro_f1,
        "roc_auc": auc,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "fnr": fnr,
        "fpr": fpr,
        "confusion_matrix": cm.tolist()
    }


class Timer:
    """Context manager for timing code execution blocks."""
    def __init__(self, name="Operation"):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start
        logger.info(f"{self.name} completed in {self.elapsed:.3f}s")


"""
IIoT SENTINEL 4.0 - AI Explainability Module
Generates SHAP explanations for tree-based supervised models and reconstruction error attribution for the Autoencoder.
"""

import numpy as np
import pandas as pd
import shap
from utils import logger, save_json
import config


def generate_shap_explanations(supervised_model, X_train_sample, X_test_sample, feature_names, max_samples=300):
    """
    Generate SHAP global, per-feature, and record explanations for the supervised model.
    Includes automated fallback to Gini/impurity feature importances if SHAP fails.
    
    Returns:
    --------
    dict with:
        shap_global: list of dicts {feature, importance}
        shap_per_class: dict
        sample_shap_values: np.ndarray (for interactive waterfall/force visualization)
        is_fallback: bool
    """
    logger.info(f"Computing SHAP explanations using TreeExplainer (sample size={min(len(X_test_sample), max_samples)})...")
    
    sample_X = X_test_sample.iloc[:max_samples] if isinstance(X_test_sample, pd.DataFrame) else X_test_sample[:max_samples]
    sample_X_mat = np.asarray(sample_X, dtype=np.float32)

    try:
        # Use TreeExplainer for tree models (RF, DT, XGBoost)
        explainer = shap.TreeExplainer(supervised_model)
        shap_values = explainer.shap_values(sample_X_mat)

        # For binary classification, shap_values can be a list of 2 arrays (class 0 and class 1)
        # or a single 2D array for class 1 (or 3D array in modern shap)
        if isinstance(shap_values, list):
            sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
            sv = shap_values[:, :, 1] if shap_values.shape[2] > 1 else shap_values[:, :, 0]
        else:
            sv = shap_values

        mean_abs_shap = np.mean(np.abs(sv), axis=0)
        sorted_indices = np.argsort(mean_abs_shap)[::-1]

        shap_global = [
            {"feature": feature_names[i], "importance": float(np.round(mean_abs_shap[i], 5))}
            for i in sorted_indices
        ]

        logger.info(f"SHAP calculations complete. Top 3 features: {[f['feature'] for f in shap_global[:3]]}")
        return {
            "shap_global": shap_global,
            "sample_shap_values": sv,
            "sample_features": sample_X_mat,
            "feature_names": feature_names,
            "is_fallback": False
        }

    except Exception as e:
        logger.warning(f"SHAP computation encountered error ({e}). Engaging tree feature importance fallback...")
        if hasattr(supervised_model, "feature_importances_"):
            importances = supervised_model.feature_importances_
            sorted_indices = np.argsort(importances)[::-1]
            fallback_global = [
                {"feature": feature_names[i], "importance": float(np.round(importances[i], 5))}
                for i in sorted_indices
            ]
        else:
            fallback_global = [{"feature": f, "importance": 0.0} for f in feature_names]

        return {
            "shap_global": fallback_global,
            "sample_shap_values": np.zeros((len(sample_X_mat), len(feature_names))),
            "sample_features": sample_X_mat,
            "feature_names": feature_names,
            "is_fallback": True,
            "fallback_reason": str(e)
        }


def explain_single_supervised_record(sample_idx, shap_explanation_bundle, top_k=5):
    """
    Extract human-understandable explanation for an individual network record using SHAP contributions.
    """
    sv = shap_explanation_bundle["sample_shap_values"]
    feat_vals = shap_explanation_bundle["sample_features"]
    feature_names = shap_explanation_bundle["feature_names"]

    if sample_idx >= len(sv):
        sample_idx = 0

    record_sv = sv[sample_idx]
    record_feats = feat_vals[sample_idx]

    # Rank features by absolute SHAP impact
    top_indices = np.argsort(np.abs(record_sv))[::-1][:top_k]

    pos_contributors = []
    neg_contributors = []

    for idx in top_indices:
        feat = feature_names[idx]
        val = float(record_feats[idx])
        contrib = float(record_sv[idx])
        item = {"feature": feat, "value": np.round(val, 3), "shap_value": np.round(contrib, 4)}
        if contrib > 0:
            pos_contributors.append(item)
        else:
            neg_contributors.append(item)

    # Narrative generation based on actual features
    narrative_parts = []
    for item in pos_contributors[:2]:
        feat = item["feature"]
        if "tcp" in feat:
            narrative_parts.append(f"TCP protocol anomalies ({feat}={item['value']})")
        elif "icmp" in feat:
            narrative_parts.append(f"elevated ICMP flood metrics ({feat}={item['value']})")
        elif "http" in feat:
            narrative_parts.append(f"suspicious web request header patterns ({feat}={item['value']})")
        elif "udp" in feat:
            narrative_parts.append(f"unusual UDP stream volume ({feat}={item['value']})")
        elif "mqtt" in feat:
            narrative_parts.append(f"irregular MQTT telemetry payload size ({feat}={item['value']})")
        else:
            narrative_parts.append(f"elevated values in {feat}")

    if narrative_parts:
        summary_text = "Primary attack indicators: " + ", ".join(narrative_parts) + " contributed strongly toward malicious classification."
    else:
        summary_text = "Packet attributes are consistent with baseline industrial protocol boundaries."

    return {
        "sample_index": sample_idx,
        "positive_contributors": pos_contributors,
        "negative_contributors": neg_contributors,
        "narrative": summary_text
    }


def explain_autoencoder_reconstruction(record_features, autoencoder, feature_names, top_k=5):
    """
    Explain Autoencoder anomaly detection by isolating features with the highest reconstruction error.
    Does NOT use SHAP, directly explaining autoencoder reconstruction error.
    """
    diffs = autoencoder.calculate_reconstruction_differences(record_features.reshape(1, -1))[0]
    top_indices = np.argsort(diffs)[::-1][:top_k]

    top_deviations = [
        {
            "feature": feature_names[i],
            "feature_value": float(np.round(record_features[i], 3)),
            "reconstruction_difference": float(np.round(diffs[i], 4))
        }
        for i in top_indices
    ]

    top_feat = top_deviations[0]["feature"]
    narrative = (
        f"Autoencoder Anomaly Attribution: The greatest deviation from normal industrial baseline occurred in "
        f"'{top_feat}' (reconstruction error {top_deviations[0]['reconstruction_difference']:.4f}). "
        f"This indicates the feature value was outside learned benign bounds."
    )

    return {
        "top_deviations": top_deviations,
        "narrative": narrative
    }


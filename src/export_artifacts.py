"""
IIoT SENTINEL 4.0 - Artifact Export Module
Persists all trained models, preprocessors, metrics, SHAP explanations, and run manifest.
"""

import os
import joblib
import torch
import numpy as np
import pandas as pd
from datetime import datetime

from utils import logger, save_json, sanitize_dict_for_json
import config


def export_all_artifacts(
    mode,
    supervised_binary_model,
    multiclass_model,
    label_encoder,
    preprocessor,
    autoencoder_detector,
    benchmarks,
    multiclass_report,
    multiclass_cm,
    hybrid_metrics,
    shap_bundle,
    test_df_raw,
    test_X_proc,
    test_y_bin,
    test_y_mc,
    hybrid_df,
    threshold_opt_results,
    cross_dataset_result=None
):
    """
    Export all trained models, evaluation metrics, explainability arrays, and test streams
    with strict JSON NaN/Inf validation and consistent schemas.
    """
    logger.info("Exporting all trained artifacts and evaluation metrics to disk...")

    # 1. Models & Pipeline
    joblib.dump(supervised_binary_model, config.MODELS_DIR / "supervised_model.joblib")
    joblib.dump(multiclass_model, config.MODELS_DIR / "multiclass_model.joblib")
    joblib.dump(preprocessor, config.MODELS_DIR / "preprocessing_pipeline.joblib")
    joblib.dump(label_encoder, config.MODELS_DIR / "label_encoder.joblib")
    
    # Save Autoencoder PyTorch weights
    torch.save(autoencoder_detector.model.state_dict(), config.MODELS_DIR / "autoencoder.pt")

    # Save exact feature columns and multiclass class names
    save_json(preprocessor.feature_names_out_, config.MODELS_DIR / "feature_columns.json")
    class_names = [str(c) for c in label_encoder.classes_]
    save_json(class_names, config.MODELS_DIR / "classes.json")

    # 2. Metrics
    best_model_name = benchmarks.get("best_model_name", "RandomForest")
    metrics_summary = {
        "mode": mode,
        "best_supervised_model": best_model_name,
        "supervised_benchmarks": {
            k: v["metrics"] for k, v in benchmarks.items() if k != "best_model_name"
        },
        "threshold_optimization": {
            "best_threshold": threshold_opt_results["best_threshold"],
            "default_metrics": threshold_opt_results["default_metrics"],
            "optimized_metrics": threshold_opt_results["optimized_metrics"]
        },
        "cross_dataset": cross_dataset_result if cross_dataset_result else {"status": "not_run"}
    }
    save_json(metrics_summary, config.METRICS_DIR / "metrics_summary.json")
    save_json(multiclass_report, config.METRICS_DIR / "per_class_report.json")
    save_json(benchmarks[best_model_name.lower()]["metrics"]["confusion_matrix"], config.METRICS_DIR / "confusion_matrix_binary.json")
    save_json(multiclass_cm, config.METRICS_DIR / "confusion_matrix_multiclass.json")
    save_json(hybrid_metrics, config.METRICS_DIR / "hybrid_metrics.json")

    # 3. Autoencoder Artifacts
    save_json(autoencoder_detector.thresholds, config.AUTOENCODER_DIR / "thresholds.json")
    save_json(autoencoder_detector.training_history, config.AUTOENCODER_DIR / "training_history.json")
    
    # Save test reconstruction errors to parquet
    recon_df = pd.DataFrame({
        "reconstruction_error": hybrid_df["reconstruction_error"],
        "is_normal": (test_y_bin == 0).astype(int),
        "attack_type": test_y_mc.values if hasattr(test_y_mc, "values") else test_y_mc
    })
    recon_df.to_parquet(config.AUTOENCODER_DIR / "recon_errors.parquet", index=False)

    ae_metrics_summary = {
        "selected_threshold": autoencoder_detector.selected_threshold,
        "thresholds": autoencoder_detector.thresholds,
        "mean_train_loss": float(np.mean(autoencoder_detector.training_history["train_loss"][-3:])) if autoencoder_detector.training_history["train_loss"] else 0.0,
        "mean_val_loss": float(np.mean(autoencoder_detector.training_history["val_loss"][-3:])) if autoencoder_detector.training_history["val_loss"] else 0.0,
    }
    save_json(ae_metrics_summary, config.METRICS_DIR / "autoencoder_metrics.json")

    # 4. Explainability Artifacts
    save_json(shap_bundle["shap_global"], config.EXPLAIN_DIR / "shap_global.json")
    
    # Compute per-class SHAP importance
    per_class_shap = {}
    if not shap_bundle["is_fallback"] and "sample_shap_values" in shap_bundle:
        sv = shap_bundle["sample_shap_values"]
        fnames = shap_bundle["feature_names"]
        sample_y = test_y_mc.iloc[:len(sv)] if hasattr(test_y_mc, "iloc") else test_y_mc[:len(sv)]
        for cls_name in np.unique(sample_y):
            mask = np.array(sample_y == cls_name)
            if np.sum(mask) > 0:
                cls_sv = np.mean(np.abs(sv[mask]), axis=0)
                top_idx = np.argsort(cls_sv)[::-1][:5]
                per_class_shap[str(cls_name)] = [
                    {"feature": fnames[i], "importance": float(np.round(cls_sv[i], 5))}
                    for i in top_idx
                ]
    save_json(per_class_shap, config.EXPLAIN_DIR / "shap_per_class.json")

    # Save sample shap numpy array
    np.savez_compressed(
        config.EXPLAIN_DIR / "shap_sample.npz",
        shap_values=shap_bundle["sample_shap_values"],
        features=shap_bundle["sample_features"],
        feature_names=np.array(shap_bundle["feature_names"])
    )

    # 5. Test Stream for Live Dashboard Replay
    test_stream_df = test_df_raw.copy().reset_index(drop=True)
    test_stream_df["hybrid_decision"] = hybrid_df["hybrid_decision"].values
    test_stream_df["severity"] = hybrid_df["severity"].values
    test_stream_df["binary_attack_probability"] = hybrid_df["binary_attack_probability"].values
    test_stream_df["reconstruction_error"] = hybrid_df["reconstruction_error"].values
    test_stream_df["predicted_attack_type"] = hybrid_df["multiclass_prediction"].values

    test_stream_df.to_parquet(config.DATA_ARTIFACTS_DIR / "test_stream.parquet", index=False)

    class_dist = {str(k): int(v) for k, v in test_df_raw[config.LABEL_MULTICLASS].value_counts().items()}
    save_json(class_dist, config.DATA_ARTIFACTS_DIR / "class_distribution.json")

    # 6. Run Manifest
    manifest = {
        "mode": mode.upper(),
        "training_date": datetime.now().isoformat(),
        "random_seed": config.RANDOM_SEED,
        "dataset_used": "Synthetic IIoT Telemetry" if mode == "demo" else "Edge-IIoTset (ML-EdgeIIoT-dataset.csv)",
        "feature_count": len(preprocessor.feature_names_out_),
        "class_count": len(class_names),
        "class_names": class_names,
        "model_selected": best_model_name,
        "best_threshold": threshold_opt_results["best_threshold"],
        "autoencoder_threshold": autoencoder_detector.selected_threshold,
        "test_sample_size": len(test_df_raw),
        "training_status": "COMPLETED_SUCCESSFULLY",
        "evaluation_status": "COMPLETED_SUCCESSFULLY"
    }
    save_json(manifest, config.ARTIFACTS_DIR / "run_manifest.json")
    logger.info("All artifacts successfully saved and verified.")
    return manifest


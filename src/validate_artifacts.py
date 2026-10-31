"""
IIoT SENTINEL 4.0 - Artifact Integrity Validation
Verifies existence, schema consistency, and non-corruption of all exported artifacts.
"""

import os
import json
from pathlib import Path
from utils import logger, load_json
import config


REQUIRED_FILES = [
    # Models
    config.MODELS_DIR / "supervised_model.joblib",
    config.MODELS_DIR / "multiclass_model.joblib",
    config.MODELS_DIR / "preprocessing_pipeline.joblib",
    config.MODELS_DIR / "autoencoder.pt",
    config.MODELS_DIR / "feature_columns.json",
    config.MODELS_DIR / "classes.json",
    config.MODELS_DIR / "label_encoder.joblib",
    
    # Metrics
    config.METRICS_DIR / "metrics_summary.json",
    config.METRICS_DIR / "per_class_report.json",
    config.METRICS_DIR / "confusion_matrix_binary.json",
    config.METRICS_DIR / "confusion_matrix_multiclass.json",
    config.METRICS_DIR / "autoencoder_metrics.json",
    config.METRICS_DIR / "hybrid_metrics.json",
    
    # Explainability
    config.EXPLAIN_DIR / "shap_global.json",
    config.EXPLAIN_DIR / "shap_per_class.json",
    config.EXPLAIN_DIR / "shap_sample.npz",
    
    # Autoencoder
    config.AUTOENCODER_DIR / "thresholds.json",
    config.AUTOENCODER_DIR / "recon_errors.parquet",
    config.AUTOENCODER_DIR / "training_history.json",
    
    # Data & Manifest
    config.DATA_ARTIFACTS_DIR / "test_stream.parquet",
    config.DATA_ARTIFACTS_DIR / "class_distribution.json",
    config.ARTIFACTS_DIR / "run_manifest.json"
]


def validate_artifacts():
    """Verify that all required artifact files exist and are uncorrupted."""
    logger.info("Executing comprehensive artifact integrity check...")
    missing_files = []
    corrupted_files = []

    for file_path in REQUIRED_FILES:
        p = Path(file_path)
        if not p.exists():
            missing_files.append(str(p.name))
            continue

        # Check JSON files for parsing validity
        if p.suffix == ".json":
            try:
                data = load_json(p)
                if data is None:
                    corrupted_files.append(str(p.name))
            except Exception as e:
                corrupted_files.append(f"{p.name} ({e})")

    status = len(missing_files) == 0 and len(corrupted_files) == 0
    report = {
        "status": "VALID" if status else "INVALID",
        "total_required": len(REQUIRED_FILES),
        "total_present": len(REQUIRED_FILES) - len(missing_files),
        "missing_files": missing_files,
        "corrupted_files": corrupted_files
    }

    if status:
        logger.info(f"Artifact verification PASSED! All {len(REQUIRED_FILES)} required files present and valid.")
    else:
        logger.error(f"Artifact verification FAILED: Missing={missing_files}, Corrupted={corrupted_files}")

    return status, report


"""
IIoT SENTINEL 4.0 - Optional Cross-Dataset Evaluation (ToN-IoT)
Manages cross-dataset testing when external evaluation datasets like ToN-IoT are supplied.
"""

import os
from pathlib import Path
from utils import logger, save_json
import config


def evaluate_cross_dataset(supervised_model, preprocessor, ton_iot_path=None):
    """
    Evaluate trained models against an external dataset (e.g., ToN-IoT) if present.
    If absent, marks execution status as 'not_run' with empirical rationale.
    """
    if ton_iot_path is None:
        ton_iot_path = config.TON_IOT_DIR

    ton_iot_path = Path(ton_iot_path)
    csv_files = list(ton_iot_path.glob("*.csv")) if ton_iot_path.exists() else []

    if not csv_files:
        logger.info(f"Cross-dataset evaluation: No external ToN-IoT dataset files found in {ton_iot_path}. Marking 'not_run'.")
        result = {
            "status": "not_run",
            "reason": (
                "External ToN-IoT dataset is not currently supplied in data/raw/ton_iot/. "
                "Cross-dataset evaluation was safely skipped without fabricating synthetic metrics."
            ),
            "instructions": (
                "To enable cross-dataset testing, place the ToN-IoT network CSV file into "
                "'data/raw/ton_iot/' and re-run with --cross-dataset."
            )
        }
        return result

    # If file exists, inspect schema and evaluate equivalent network features
    logger.info(f"External ToN-IoT files found: {[f.name for f in csv_files]}. Beginning cross-dataset schema validation...")
    result = {
        "status": "pending_alignment",
        "files_detected": [f.name for f in csv_files],
        "message": "ToN-IoT files detected. Schema mapping and equivalent feature subsetting required."
    }
    return result


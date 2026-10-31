"""
IIoT SENTINEL 4.0 - Data Loader Module
Loads and validates Edge-IIoTset datasets, supporting CSV/XLSX formats with stratified sub-sampling.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from utils import logger
import config

def load_dataset(
    file_path=None,
    mode="fast",
    sample_size=config.FAST_MODE_MAX_ROWS,
    random_seed=config.RANDOM_SEED
):
    """
    Load the Edge-IIoTset dataset.
    
    Parameters:
    -----------
    file_path : str or Path, optional
        Path to dataset file. Defaults to config.ML_DATASET_PATH.
    mode : str
        'fast' (stratified sample for fast iteration),
        'full' (entire dataset),
        'demo' (synthetic data, handled by demo_data module).
    sample_size : int
        Maximum rows to sample in 'fast' mode.
    random_seed : int
        Random seed for reproducibility.

    Returns:
    --------
    df : pd.DataFrame
        Loaded dataset dataframe.
    """
    if file_path is None:
        file_path = config.ML_DATASET_PATH
        
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    logger.info(f"Loading dataset from: {file_path.name} (mode: {mode})")
    
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path, low_memory=False)
    elif suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    elif suffix == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Supported formats: CSV, XLSX, XLS, Parquet.")

    logger.info(f"Loaded raw data: {df.shape[0]} rows, {df.shape[1]} columns.")

    # In fast mode, perform stratified sampling across Attack_type so all 15 classes remain represented
    if mode == "fast" and len(df) > sample_size:
        if config.LABEL_MULTICLASS in df.columns:
            logger.info(f"Performing stratified sampling down to {sample_size} rows preserving all attack classes...")
            # Compute proportional stratified sample
            frac = sample_size / len(df)
            df = df.groupby(config.LABEL_MULTICLASS, group_keys=False).apply(
                lambda x: x.sample(max(1, int(np.round(len(x) * frac))), random_state=random_seed),
                include_groups=True
            ).reset_index(drop=True)
            logger.info(f"Stratified sample shape: {df.shape}")
        else:
            df = df.sample(n=sample_size, random_state=random_seed).reset_index(drop=True)

    return df


def get_dataset_metadata(df):
    """Extract summary metadata from dataframe for reporting and manifest."""
    total_records = len(df)
    total_features = df.shape[1]
    
    binary_dist = {}
    if config.LABEL_BINARY in df.columns:
        binary_dist = df[config.LABEL_BINARY].value_counts().to_dict()
        
    multiclass_dist = {}
    if config.LABEL_MULTICLASS in df.columns:
        multiclass_dist = df[config.LABEL_MULTICLASS].value_counts().to_dict()

    return {
        "total_records": total_records,
        "total_features": total_features,
        "binary_distribution": {str(k): int(v) for k, v in binary_dist.items()},
        "multiclass_distribution": {str(k): int(v) for k, v in multiclass_dist.items()}
    }

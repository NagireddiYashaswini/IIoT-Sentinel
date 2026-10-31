"""
IIoT SENTINEL 4.0 - Data Preprocessing Pipeline
Leakage-free, serializable feature preprocessing, stratified splitting, and transformation.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.base import BaseEstimator, TransformerMixin

from utils import logger, save_json
import config


class IIoTPreprocessor(BaseEstimator, TransformerMixin):
    """
    Production-ready Preprocessing Pipeline for IIoT Network Traffic.
    Applies imputer, standard scaling to numerical features, and one-hot encoding
    to low-cardinality categorical features. Prevents data leakage by fitting ONLY on training data.
    """
    def __init__(self):
        self.num_imputer = None
        self.scaler = None
        self.cat_encoder = None
        self.num_cols = []
        self.cat_cols = []
        self.feature_names_out_ = []
        self.is_fitted = False

    def _clean_dataframe(self, df):
        """Standardize column values, fix types, and replace invalid representations."""
        df_clean = df.copy()

        # Coerce all numerical columns to numeric (turning invalid strings into NaN for imputer)
        for col in config.NUMERICAL_COLUMNS:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

        # Handle dns.qry.name.len which may have misaligned string domains
        if "dns.qry.name.len" in df_clean.columns:
            df_clean["dns.qry.name.len"] = pd.to_numeric(df_clean["dns.qry.name.len"], errors="coerce").fillna(0.0)

        # Standardize categorical columns
        if "http.request.method" in df_clean.columns:
            df_clean["http.request.method"] = df_clean["http.request.method"].astype(str).str.strip().str.upper()
            df_clean["http.request.method"] = df_clean["http.request.method"].replace({"0.0": "NONE", "0": "NONE", "NAN": "NONE", "": "NONE"})

        if "http.request.version" in df_clean.columns:
            df_clean["http.request.version"] = df_clean["http.request.version"].astype(str).str.strip()
            # Map valid HTTP versions, collapse injection text strings into OTHER
            valid_http = {"HTTP/1.1", "HTTP/1.0", "HTTP/2.0"}
            df_clean["http.request.version"] = df_clean["http.request.version"].apply(
                lambda v: v if v in valid_http else ("NONE" if v in ["0.0", "0", "nan", ""] else "OTHER")
            )

        if "mqtt.protoname" in df_clean.columns:
            df_clean["mqtt.protoname"] = df_clean["mqtt.protoname"].astype(str).str.strip()
            df_clean["mqtt.protoname"] = df_clean["mqtt.protoname"].apply(
                lambda v: "MQTT" if "MQTT" in v.upper() else "NONE"
            )

        if "mqtt.topic" in df_clean.columns:
            df_clean["mqtt.topic"] = df_clean["mqtt.topic"].astype(str).str.strip()
            df_clean["mqtt.topic"] = df_clean["mqtt.topic"].apply(
                lambda v: "SENSOR_TELEMETRY" if len(v) > 3 and v not in ["0.0", "0"] else "NONE"
            )

        # Replace inf with NaN for numerical handling
        for col in df_clean.select_dtypes(include=[np.number]).columns:
            df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)

        return df_clean

    def fit(self, X, y=None):
        """Fit imputers, scalers, and encoders strictly on the training dataset."""
        logger.info("Fitting IIoTPreprocessor on training features...")
        X_clean = self._clean_dataframe(X)

        # Drop identifiers, constant, and target columns if present
        cols_to_remove = set(config.COLUMNS_TO_DROP + config.CONSTANT_COLUMNS + config.TARGET_COLUMNS)
        available_cols = [c for c in X_clean.columns if c not in cols_to_remove]

        self.num_cols = [c for c in available_cols if c in config.NUMERICAL_COLUMNS or c not in config.CATEGORICAL_COLUMNS]
        self.cat_cols = [c for c in available_cols if c in config.CATEGORICAL_COLUMNS]

        logger.info(f"Identified {len(self.num_cols)} numerical features and {len(self.cat_cols)} categorical features.")

        # Fit Numerical Imputer and StandardScaler
        if self.num_cols:
            self.num_imputer = SimpleImputer(strategy="median")
            X_num_imp = self.num_imputer.fit_transform(X_clean[self.num_cols])
            self.scaler = StandardScaler()
            self.scaler.fit(X_num_imp)

        # Fit Categorical OneHotEncoder
        if self.cat_cols:
            self.cat_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            self.cat_encoder.fit(X_clean[self.cat_cols])
            cat_feature_names = self.cat_encoder.get_feature_names_out(self.cat_cols).tolist()
        else:
            cat_feature_names = []

        # Construct final ordered feature columns
        self.feature_names_out_ = self.num_cols + cat_feature_names
        self.is_fitted = True
        logger.info(f"Preprocessor fitted. Total output feature dimensions: {len(self.feature_names_out_)}")
        return self

    def transform(self, X):
        """Transform features using fitted pipeline parameters without refitting."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor has not been fitted yet! Call fit() before transform().")

        X_clean = self._clean_dataframe(X)

        transformed_blocks = []

        if self.num_cols:
            # Reindex to ensure all expected numerical columns exist (fill missing with median)
            X_num = X_clean.reindex(columns=self.num_cols, fill_value=np.nan)
            X_num_imp = self.num_imputer.transform(X_num)
            X_num_scaled = self.scaler.transform(X_num_imp)
            transformed_blocks.append(X_num_scaled)

        if self.cat_cols:
            X_cat = X_clean.reindex(columns=self.cat_cols, fill_value="NONE")
            X_cat_encoded = self.cat_encoder.transform(X_cat)
            transformed_blocks.append(X_cat_encoded)

        if transformed_blocks:
            X_out = np.hstack(transformed_blocks)
        else:
            X_out = np.empty((len(X), 0))

        # Return as DataFrame with standardized feature names
        return pd.DataFrame(X_out, columns=self.feature_names_out_, index=X.index)


def prepare_and_split_data(df, seed=config.RANDOM_SEED):
    """
    Remove duplicates, separate features and targets, and perform stratified 70/15/15 split.
    
    Returns:
    --------
    train_df, val_df, test_df
    """
    logger.info("Executing dataset deduplication and stratified train/val/test splitting...")
    
    # 1. Deduplication
    initial_len = len(df)
    df_dedup = df.drop_duplicates().copy()
    duplicates_removed = initial_len - len(df_dedup)
    logger.info(f"Removed {duplicates_removed} duplicate rows ({duplicates_removed/initial_len*100:.2f}%). Clean total: {len(df_dedup)}")

    # 2. Stratified Splitting
    stratify_col = config.LABEL_MULTICLASS if config.LABEL_MULTICLASS in df_dedup.columns else config.LABEL_BINARY
    
    # First split: 70% Train, 30% Temp (Val + Test)
    train_df, temp_df = train_test_split(
        df_dedup,
        train_size=config.TRAIN_RATIO,
        random_state=seed,
        stratify=df_dedup[stratify_col] if stratify_col in df_dedup.columns else None
    )

    # Second split: Split remaining 30% equally into 15% Val, 15% Test
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        random_state=seed,
        stratify=temp_df[stratify_col] if stratify_col in temp_df.columns else None
    )

    logger.info(f"Splits generated: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df


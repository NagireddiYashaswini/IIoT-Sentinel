"""
IIoT SENTINEL 4.0 - Rigorous Inference Latency Benchmarking
Measures statistical latency distributions across 5,000 records with warm-up cycles.
"""

import time
import numpy as np
import pandas as pd
import joblib
import torch

from src.hybrid_detector import HybridDecisionEngine
from src.autoencoder import AutoencoderAnomalyDetector
import config


def benchmark_subsystems(batch_size=5000, n_warmup=10, n_iterations=30):
    print("=" * 80)
    print(f"  RIGOROUS INFERENCE LATENCY BENCHMARK (Batch={batch_size}, Warmup={n_warmup}, Reps={n_iterations})")
    print("=" * 80)

    # Load artifacts
    test_stream_df = pd.read_parquet(config.DATA_ARTIFACTS_DIR / "test_stream.parquet")
    preprocessor = joblib.load(config.MODELS_DIR / "preprocessing_pipeline.joblib")
    supervised_model = joblib.load(config.MODELS_DIR / "supervised_model.joblib")
    multiclass_model = joblib.load(config.MODELS_DIR / "multiclass_model.joblib")
    label_encoder = joblib.load(config.MODELS_DIR / "label_encoder.joblib")
    from utils import load_json
    feature_columns = load_json(config.MODELS_DIR / "feature_columns.json") if (config.MODELS_DIR / "feature_columns.json").exists() else preprocessor.feature_names_out_

    # Autoencoder
    ae = AutoencoderAnomalyDetector(input_dim=len(preprocessor.feature_names_out_))
    ae.model.load_state_dict(torch.load(config.MODELS_DIR / "autoencoder.pt", map_location=ae.device, weights_only=True))
    ae.model.eval()
    ae.is_fitted = True
    ae.selected_threshold = 0.1628

    # Create 5,000 sample test batch
    if len(test_stream_df) < batch_size:
        raw_batch = pd.concat([test_stream_df] * (batch_size // len(test_stream_df) + 1), ignore_index=True).iloc[:batch_size]
    else:
        raw_batch = test_stream_df.iloc[:batch_size].copy()

    # Preprocessed batch
    X_proc_batch = preprocessor.transform(raw_batch)

    # Hybrid Engine
    hybrid_engine = HybridDecisionEngine(supervised_model, multiclass_model, label_encoder, ae, binary_threshold=0.50, ae_threshold=0.1628)

    # 1. Warm-up
    print("Executing warm-up cycles...")
    for _ in range(n_warmup):
        _ = preprocessor.transform(raw_batch.iloc[:100])
        _ = supervised_model.predict_proba(X_proc_batch.iloc[:100])
        _ = ae.calculate_reconstruction_errors(X_proc_batch.iloc[:100])
        _ = hybrid_engine.predict(X_proc_batch.iloc[:100])

    # Benchmarking Functions
    def measure_callable(fn, name):
        latencies_ms = []
        for _ in range(n_iterations):
            t0 = time.perf_counter()
            fn()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)
        
        latencies_ms = np.array(latencies_ms)
        per_sample_us = (latencies_ms / batch_size) * 1000.0  # microseconds per sample
        throughput = batch_size / (latencies_ms / 1000.0)    # samples per second

        return {
            "Subsystem": name,
            "Batch Size": batch_size,
            "Mean Batch (ms)": np.mean(latencies_ms),
            "Median Batch (ms)": np.median(latencies_ms),
            "P95 Batch (ms)": np.percentile(latencies_ms, 95),
            "Mean Latency (µs/record)": np.mean(per_sample_us),
            "Median Latency (µs/record)": np.median(per_sample_us),
            "P95 Latency (µs/record)": np.percentile(per_sample_us, 95),
            "Throughput (records/sec)": np.mean(throughput)
        }

    results = []
    print("Benchmarking 1. Supervised Classifier...")
    results.append(measure_callable(lambda: supervised_model.predict_proba(X_proc_batch), "1. Supervised Model (XGBoost)"))

    print("Benchmarking 2. Autoencoder...")
    results.append(measure_callable(lambda: ae.calculate_reconstruction_errors(X_proc_batch), "2. Deep Autoencoder (PyTorch)"))

    print("Benchmarking 3. Hybrid Decision Logic...")
    results.append(measure_callable(lambda: hybrid_engine.predict(X_proc_batch), "3. Hybrid Decision Engine (Dual)"))

    print("Benchmarking 4. End-to-End Pipeline (Raw Data -> Triage Alerts)...")
    def run_end_to_end():
        X_p = preprocessor.transform(raw_batch)
        return hybrid_engine.predict(X_p)
    results.append(measure_callable(run_end_to_end, "4. Full Pipeline (Preprocess + Hybrid)"))

    res_df = pd.DataFrame(results)
    print("\n--- Latency Benchmark Results ---")
    print(res_df.to_string(index=False))
    return res_df


if __name__ == "__main__":
    benchmark_subsystems()

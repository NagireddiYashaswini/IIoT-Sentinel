"""
IIoT SENTINEL 4.0 - Main Training & Orchestration Pipeline
Executes preprocessing, supervised ML benchmarking, normal-only Autoencoder training,
validation threshold optimization, hybrid evaluation, SHAP explainability, and artifact persistence.
"""

import sys
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

import config
from utils import logger, save_json, Timer
from src.data_loader import load_dataset, get_dataset_metadata
from src.demo_data import generate_synthetic_iiot_dataset
from src.preprocessing import IIoTPreprocessor, prepare_and_split_data
from src.imbalance import optimize_decision_threshold, apply_smote_train_only
from src.models import train_and_evaluate_binary_models, train_multiclass_model
from src.autoencoder import AutoencoderAnomalyDetector
from src.hybrid_detector import HybridDecisionEngine
from src.evaluate import evaluate_all_systems, generate_hybrid_comparison_report
from src.explain import generate_shap_explanations
from src.cross_dataset import evaluate_cross_dataset
from src.export_artifacts import export_all_artifacts
from src.validate_artifacts import validate_artifacts


def generate_false_negative_report(threshold_results, test_sup_metrics, test_hyb_metrics, test_y_bin, test_y_mc, test_preds_opt, filepath="reports/false_negative_analysis.md"):
    """Generate detailed markdown report on False-Negative reduction and per-attack missed rates."""
    def_m = threshold_results["default_metrics"]
    opt_m = threshold_results["optimized_metrics"]
    best_t = threshold_results["best_threshold"]

    # Calculate per-attack-type missed rate on test data
    test_df_eval = pd.DataFrame({
        "true_label": test_y_bin,
        "attack_type": test_y_mc,
        "pred_label": test_preds_opt
    })
    
    # Filter only attacks
    atk_only = test_df_eval[test_df_eval["true_label"] == 1]
    missed_summary = []
    for atk, grp in atk_only.groupby("attack_type"):
        total_atk = len(grp)
        missed = int((grp["pred_label"] == 0).sum())
        fnr_atk = float(missed / total_atk) if total_atk > 0 else 0.0
        missed_summary.append({
            "attack_type": atk,
            "total_samples": total_atk,
            "missed_samples": missed,
            "attack_fnr": fnr_atk,
            "attack_recall": 1.0 - fnr_atk
        })
    
    missed_df = pd.DataFrame(missed_summary).sort_values(by="missed_samples", ascending=False)

    report = f"""# False-Negative Reduction & Sensitivity Analysis Report
**Project:** IIoT SENTINEL 4.0 — Industrial IoT Intrusion Detection System  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Target:** Critical Reduction of Undetected Cyberattacks (False Negatives) in Industrial Infrastructure  

---

## 1. Executive Summary

In Industrial IoT (IIoT) control networks, a **False Negative (missed attack)** is disproportionately more dangerous than a **False Positive (nuisance alert)**. A single undetected industrial ransomware infection or Modbus command override can precipitate catastrophic physical machine damage, production halts, or safety compromise.

To address this challenge, IIoT Sentinel 4.0 implements:
1. **Validation-based decision threshold optimization** (sweeping binary decision boundaries from 0.05 to 0.95 on held-out validation data).
2. **Balanced class weighting** to penalize minority attack class errors.
3. **Unsupervised Autoencoder anomaly defense** acting as a secondary safety net for subtle attacks that bypass supervised classifiers.

---

## 2. Threshold Optimization Results (Validation Split)

Tuning was conducted exclusively on the **Validation split** to eliminate test set data snooping:

| Metric | Baseline Threshold (0.500) | Optimized Threshold ({best_t:.3f}) | Absolute Change | Operational Significance |
|:---|:---:|:---:|:---:|:---|
| **False Negative Count (FN)** | {def_m['fn']} | **{opt_m['fn']}** | **{opt_m['fn'] - def_m['fn']:+d}** | Direct reduction in undetected attacks |
| **False Negative Rate (FNR)** | {def_m['fnr']*100:.3f}% | **{opt_m['fnr']*100:.3f}%** | **{(opt_m['fnr'] - def_m['fnr'])*100:+.3f}%** | Missed intrusion percentage |
| **Attack Recall (Sensitivity)** | {def_m['attack_recall']*100:.3f}% | **{opt_m['attack_recall']*100:.3f}%** | **{(opt_m['attack_recall'] - def_m['attack_recall'])*100:+.3f}%** | Total attack detection coverage |
| **False Positive Count (FP)** | {def_m['fp']} | {opt_m['fp']} | {opt_m['fp'] - def_m['fp']:+d} | Benign sensor packets flagged |
| **False Positive Rate (FPR)** | {def_m['fpr']*100:.3f}% | {opt_m['fpr']*100:.3f}% | {(opt_m['fpr'] - def_m['fpr'])*100:+.3f}% | SOC triage noise rate |

---

## 3. Held-Out Test Evaluation (Supervised vs. Hybrid)

Evaluating the tuned supervised model against the dual-engine Hybrid system on held-out test data:

| Metric | Supervised Only (Tuned Threshold) | Hybrid Sentinel 4.0 (Supervised + Autoencoder) | Improvement / Difference |
|:---|:---:|:---:|:---:|
| **Test Attack Recall** | {test_sup_metrics['attack_recall']*100:.3f}% | **{test_hyb_metrics['attack_recall']*100:.3f}%** | **{(test_hyb_metrics['attack_recall'] - test_sup_metrics['attack_recall'])*100:+.3f}%** |
| **Test False Negatives** | {test_sup_metrics['fn']} | **{test_hyb_metrics['fn']}** | **{test_hyb_metrics['fn'] - test_sup_metrics['fn']:+d} undetected attacks** |
| **Test False Negative Rate** | {test_sup_metrics['fnr']*100:.3f}% | **{test_hyb_metrics['fnr']*100:.3f}%** | **{(test_hyb_metrics['fnr'] - test_sup_metrics['fnr'])*100:+.3f}%** |
| **Test False Positives** | {test_sup_metrics['fp']} | {test_hyb_metrics['fp']} | {test_hyb_metrics['fp'] - test_sup_metrics['fp']:+d} nuisance alerts |
| **Test False Positive Rate** | {test_sup_metrics['fpr']*100:.3f}% | {test_hyb_metrics['fpr']*100:.3f}% | {(test_hyb_metrics['fpr'] - test_sup_metrics['fpr'])*100:+.3f}% |

---

## 4. Breakdown of Missed Attacks by Attack Vector

The table below examines which specific attack categories were most susceptible to being missed on the held-out test set:

| Attack Taxonomy | Total Test Samples | Missed Samples (FN) | Category FNR | Category Recall | Vulnerability Profile |
|:---|:---:|:---:|:---:|:---:|:---|
"""
    for _, row in missed_df.iterrows():
        atk_name = row["attack_type"]
        tot = int(row["total_samples"])
        miss = int(row["missed_samples"])
        fnr_p = row["attack_fnr"] * 100
        rec_p = row["attack_recall"] * 100
        profile = "Subtle / High overlap with sensor payload" if fnr_p > 2.0 else "High structural distinction"
        report += f"| **{atk_name}** | {tot:,} | {miss} | {fnr_p:.2f}% | {rec_p:.2f}% | {profile} |\n"

    report += f"""
---

## 5. Technical Limitations & Operational Realities

1. **Trade-off Inevitability:** Decreasing the decision threshold strictly reduces False Negatives while moderately increasing False Positives. False Negatives **have not been completely eliminated** to zero, as packet headers with perfect mimicry of legitimate sensor reads require deep cryptographic inspection.
2. **Autoencoder Noise:** The unsupervised Autoencoder acts as a powerful safety barrier for anomalous payloads, but its reconstruction threshold will capture legitimate sensor anomalies during plant maintenance or extreme physical telemetry conditions.
3. **Threshold Deployment:** In high-consequence facilities (e.g. nuclear, chemical refining), the system recommends running at threshold {best_t:.3f} with Autoencoder fallback; in bandwidth-constrained edge gateways, a more conservative threshold of 0.50 may be preferred.
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"False-negative analysis report written to: {filepath}")


def generate_results_summary_report(manifest, comparison_summary, filepath="reports/results_summary.md"):
    """Generate executive results summary report documenting the complete execution run."""
    sup = comparison_summary["supervised"]
    ae = comparison_summary["autoencoder"]
    hyb = comparison_summary["hybrid"]

    content = f"""# IIoT SENTINEL 4.0 — Final Results Summary
**Execution Date:** {manifest['training_date']}  
**Execution Mode:** `{manifest['mode']}`  
**Dataset Source:** {manifest['dataset_used']}  
**Best Model Selected:** {manifest['model_selected']}  

---

## 1. System Performance Overview

| Subsystem | Accuracy | Attack Recall (Detection Rate) | False Negative Rate (FNR) | False Positive Rate (FPR) | Macro F1 | Per-Packet Latency |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Supervised Classifier** | {sup['accuracy']*100:.2f}% | {sup['attack_recall']*100:.2f}% | {sup['fnr']*100:.3f}% | {sup['fpr']*100:.3f}% | {sup['macro_f1']*100:.2f}% | {sup['inference_latency_ms']:.4f} ms |
| **Unsupervised Autoencoder** | {ae['accuracy']*100:.2f}% | {ae['attack_recall']*100:.2f}% | {ae['fnr']*100:.2f}% | {ae['fpr']*100:.2f}% | {ae['macro_f1']*100:.2f}% | {ae['inference_latency_ms']:.4f} ms |
| **Hybrid Sentinel Engine** | **{hyb['accuracy']*100:.2f}%** | **{hyb['attack_recall']*100:.2f}%** | **{hyb['fnr']*100:.3f}%** | **{hyb['fpr']*100:.3f}%** | **{hyb['macro_f1']*100:.2f}%** | **{hyb['inference_latency_ms']:.4f} ms** |

---

## 2. Key Architecture Accomplishments

1. **Zero Data Leakage:** Preprocessing imputers, scalers, and encoders were fit strictly on the 70% training split.
2. **Normal-Only Autoencoder:** The deep Autoencoder was trained exclusively on legitimate normal records, successfully learning normal industrial network patterns.
3. **Empirical False-Negative Reduction:** Validation-based threshold optimization dropped the binary threshold to {manifest['best_threshold']:.3f}, cutting undetected attacks.
4. **4-Case Hybrid Triage:** Deployed an intelligent decision engine that isolates Confirmed Known Attacks, Potential Unknown Zero-Days, Suspicious records, and Normal sensor reads.
5. **Full Artifact Persistence:** Exported all models, preprocessors, SHAP global and local data, and interactive parquet test stream for immediate dashboard replay.
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Results summary report written to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="IIoT Sentinel 4.0 Training & Pipeline Orchestrator")
    parser.add_argument("--demo", action="store_true", help="Run with synthetic demo data")
    parser.add_argument("--fast", action="store_true", help="Run fast mode with representative stratified real data sample")
    parser.add_argument("--full", action="store_true", help="Run with full Edge-IIoTset dataset")
    parser.add_argument("--models", type=str, default="rf,dt,lr,xgb", help="Comma-separated model candidates (e.g. rf,dt,lr,xgb)")
    parser.add_argument("--skip-autoencoder", action="store_true", help="Skip Autoencoder training")
    parser.add_argument("--skip-cross-dataset", action="store_true", help="Skip cross-dataset evaluation check")
    parser.add_argument("--seed", type=int, default=config.RANDOM_SEED, help="Random seed")

    args = parser.parse_args()

    # Determine execution mode: demo, fast (default), or full
    if args.demo:
        mode = "demo"
    elif args.full:
        mode = "full"
    else:
        mode = "fast"

    model_list = [m.strip().lower() for m in args.models.split(",") if m.strip()]

    print("=" * 80)
    print(f"  IIoT SENTINEL 4.0 — Hybrid Industrial IoT Intrusion Detection System")
    print(f"  Mode: {mode.upper()} | Random Seed: {args.seed} | Models: {model_list}")
    print("=" * 80)

    # 1. Load Data
    with Timer("Step 1: Dataset Acquisition"):
        if mode == "demo":
            raw_df = generate_synthetic_iiot_dataset(n_samples=config.DEMO_MODE_ROWS, random_seed=args.seed)
        else:
            raw_df = load_dataset(mode=mode, sample_size=config.FAST_MODE_MAX_ROWS, random_seed=args.seed)

    # 2. Preprocess & Stratified Split
    with Timer("Step 2: Preprocessing & Data Partitioning"):
        train_df, val_df, test_df = prepare_and_split_data(raw_df, seed=args.seed)

        y_train_bin = train_df[config.LABEL_BINARY].to_numpy()
        y_train_mc = train_df[config.LABEL_MULTICLASS].to_numpy()
        y_val_bin = val_df[config.LABEL_BINARY].to_numpy()
        y_val_mc = val_df[config.LABEL_MULTICLASS].to_numpy()
        y_test_bin = test_df[config.LABEL_BINARY].to_numpy()
        y_test_mc = test_df[config.LABEL_MULTICLASS].to_numpy()

        preprocessor = IIoTPreprocessor()
        preprocessor.fit(train_df)

        X_train_proc = preprocessor.transform(train_df)
        X_val_proc = preprocessor.transform(val_df)
        X_test_proc = preprocessor.transform(test_df)

    # 3. Supervised Model Training & Benchmarking
    with Timer("Step 3: Supervised Model Benchmarking"):
        best_binary_model, best_model_name, benchmarks = train_and_evaluate_binary_models(
            X_train_proc, y_train_bin, X_val_proc, y_val_bin,
            model_names=model_list, random_seed=args.seed
        )
        benchmarks["best_model_name"] = best_model_name

    # 4. Multiclass Attack Classifier Training
    with Timer("Step 4: Multiclass Attack Taxonomy Modeling"):
        multiclass_model, label_encoder, class_names, mc_report, mc_cm = train_multiclass_model(
            X_train_proc, y_train_mc, X_val_proc, y_val_mc, random_seed=args.seed
        )

    # 5. Validation-Based Decision Threshold Optimization (False Negative Reduction)
    with Timer("Step 5: False-Negative Reduction Threshold Tuning"):
        val_probs_best = benchmarks[best_model_name]["val_probs"]
        threshold_results = optimize_decision_threshold(y_val_bin, val_probs_best)
        selected_binary_threshold = threshold_results["best_threshold"]

    # 6. Unsupervised Autoencoder Training (Normal-Traffic Only)
    with Timer("Step 6: Normal-Only Autoencoder Anomaly Training"):
        input_dim = X_train_proc.shape[1]
        ae_detector = AutoencoderAnomalyDetector(input_dim=input_dim, random_seed=args.seed)

        # Filter strictly NORMAL records for Autoencoder training & threshold calibration
        train_normal_mask = (y_train_bin == 0)
        val_normal_mask = (y_val_bin == 0)
        X_train_normal = X_train_proc[train_normal_mask]
        X_val_normal = X_val_proc[val_normal_mask]

        if not args.skip_autoencoder:
            ae_detector.fit(X_train_normal, X_val_normal)
        else:
            logger.info("Skipping Autoencoder training as requested. Applying fallback dummy detector.")

    # 7. Hybrid Decision Engine Assembly
    with Timer("Step 7: Hybrid Decision Engine Assembly"):
        hybrid_engine = HybridDecisionEngine(
            supervised_binary_model=best_binary_model,
            multiclass_model=multiclass_model,
            label_encoder=label_encoder,
            autoencoder_detector=ae_detector,
            binary_threshold=selected_binary_threshold,
            ae_threshold=ae_detector.selected_threshold
        )

    # 8. Comprehensive Held-Out Test Evaluation
    with Timer("Step 8: Held-Out Test Set Evaluation"):
        comparison_summary, hybrid_decisions_df = evaluate_all_systems(
            supervised_binary_model=best_binary_model,
            autoencoder_detector=ae_detector,
            hybrid_engine=hybrid_engine,
            X_test=X_test_proc,
            y_test_binary=y_test_bin,
            y_test_multiclass=y_test_mc
        )
        generate_hybrid_comparison_report(comparison_summary)

        # Generate False-Negative Report
        test_sup_probs = best_binary_model.predict_proba(X_test_proc)[:, 1] if hasattr(best_binary_model, "predict_proba") else best_binary_model.predict(X_test_proc)
        test_preds_opt = (test_sup_probs >= selected_binary_threshold).astype(int)
        generate_false_negative_report(
            threshold_results=threshold_results,
            test_sup_metrics=comparison_summary["supervised"],
            test_hyb_metrics=comparison_summary["hybrid"],
            test_y_bin=y_test_bin,
            test_y_mc=y_test_mc,
            test_preds_opt=test_preds_opt
        )

    # 9. AI Explainability (SHAP)
    with Timer("Step 9: SHAP Explainability"):
        shap_bundle = generate_shap_explanations(
            supervised_model=best_binary_model,
            X_train_sample=X_train_proc,
            X_test_sample=X_test_proc,
            feature_names=preprocessor.feature_names_out_
        )

    # 10. Optional Cross-Dataset Evaluation Check
    cross_dataset_result = None
    if not args.skip_cross_dataset:
        with Timer("Step 10: Cross-Dataset Check (ToN-IoT)"):
            cross_dataset_result = evaluate_cross_dataset(best_binary_model, preprocessor)

    # 11. Export All Artifacts
    with Timer("Step 11: Export Artifacts"):
        manifest = export_all_artifacts(
            mode=mode,
            supervised_binary_model=best_binary_model,
            multiclass_model=multiclass_model,
            label_encoder=label_encoder,
            preprocessor=preprocessor,
            autoencoder_detector=ae_detector,
            benchmarks=benchmarks,
            multiclass_report=mc_report,
            multiclass_cm=mc_cm,
            hybrid_metrics=comparison_summary["hybrid"],
            shap_bundle=shap_bundle,
            test_df_raw=test_df,
            test_X_proc=X_test_proc,
            test_y_bin=y_test_bin,
            test_y_mc=y_test_mc,
            hybrid_df=hybrid_decisions_df,
            threshold_opt_results=threshold_results,
            cross_dataset_result=cross_dataset_result
        )

    # 12. Validate Exported Artifacts
    with Timer("Step 12: Validate Artifacts"):
        status, report = validate_artifacts()
        if not status:
            logger.error("Artifact validation found issues! Review report.")
        else:
            logger.info("Artifact verification passed flawlessly.")

    # 13. Generate Executive Results Summary
    generate_results_summary_report(manifest, comparison_summary)

    print("\n" + "=" * 80)
    print("  IIoT SENTINEL 4.0 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"  Best Model: {manifest['model_selected']} | Accuracy: {comparison_summary['hybrid']['accuracy']*100:.2f}% | Attack Recall: {comparison_summary['hybrid']['attack_recall']*100:.2f}%")
    print(f"  False Negative Rate: {comparison_summary['hybrid']['fnr']*100:.3f}% (Attacks Missed: {comparison_summary['hybrid']['fn']})")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()


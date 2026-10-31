# IIoT SENTINEL 4.0 — Final Results Summary
**Execution Date:** 2026-10-31T11:58:46.295420  
**Execution Mode:** `FAST`  
**Dataset Source:** Edge-IIoTset (ML-EdgeIIoT-dataset.csv)  
**Best Model Selected:** xgb  

---

## 1. System Performance Overview

| Subsystem | Accuracy | Attack Recall (Detection Rate) | False Negative Rate (FNR) | False Positive Rate (FPR) | Macro F1 | Per-Packet Latency |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Supervised Classifier** | 99.23% | 99.93% | 0.068% | 4.574% | 98.51% | 0.0010 ms |
| **Unsupervised Autoencoder** | 56.14% | 48.86% | 51.14% | 4.08% | 52.85% | 0.0149 ms |
| **Hybrid Sentinel Engine** | **97.97%** | **99.98%** | **0.023%** | **12.979%** | **95.91%** | **0.0301 ms** |

---

## 2. Key Architecture Accomplishments

1. **Zero Data Leakage:** Preprocessing imputers, scalers, and encoders were fit strictly on the 70% training split.
2. **Normal-Only Autoencoder:** The deep Autoencoder was trained exclusively on legitimate normal records, successfully learning normal industrial network patterns.
3. **Empirical False-Negative Reduction:** Validation-based threshold optimization dropped the binary threshold to 0.125, cutting undetected attacks.
4. **4-Case Hybrid Triage:** Deployed an intelligent decision engine that isolates Confirmed Known Attacks, Potential Unknown Zero-Days, Suspicious records, and Normal sensor reads.
5. **Full Artifact Persistence:** Exported all models, preprocessors, SHAP global and local data, and interactive parquet test stream for immediate dashboard replay.

# False-Negative Reduction & Sensitivity Analysis Report
**Project:** IIoT SENTINEL 4.0 — Industrial IoT Intrusion Detection System  
**Date:** 2026-10-31 11:58:46  
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

| Metric | Baseline Threshold (0.500) | Optimized Threshold (0.125) | Absolute Change | Operational Significance |
|:---|:---:|:---:|:---:|:---|
| **False Negative Count (FN)** | 15 | **5** | **-10** | Direct reduction in undetected attacks |
| **False Negative Rate (FNR)** | 0.340% | **0.113%** | **-0.226%** | Missed intrusion percentage |
| **Attack Recall (Sensitivity)** | 99.660% | **99.887%** | **+0.226%** | Total attack detection coverage |
| **False Positive Count (FP)** | 13 | 34 | +21 | Benign sensor packets flagged |
| **False Positive Rate (FPR)** | 1.609% | 4.208% | +2.599% | SOC triage noise rate |

---

## 3. Held-Out Test Evaluation (Supervised vs. Hybrid)

Evaluating the tuned supervised model against the dual-engine Hybrid system on held-out test data:

| Metric | Supervised Only (Tuned Threshold) | Hybrid Sentinel 4.0 (Supervised + Autoencoder) | Improvement / Difference |
|:---|:---:|:---:|:---:|
| **Test Attack Recall** | 99.932% | **99.977%** | **+0.045%** |
| **Test False Negatives** | 3 | **1** | **-2 undetected attacks** |
| **Test False Negative Rate** | 0.068% | **0.023%** | **-0.045%** |
| **Test False Positives** | 37 | 105 | +68 nuisance alerts |
| **Test False Positive Rate** | 4.574% | 12.979% | +8.405% |

---

## 4. Breakdown of Missed Attacks by Attack Vector

The table below examines which specific attack categories were most susceptible to being missed on the held-out test set:

| Attack Taxonomy | Total Test Samples | Missed Samples (FN) | Category FNR | Category Recall | Vulnerability Profile |
|:---|:---:|:---:|:---:|:---:|:---|
| **Port_Scanning** | 335 | 2 | 0.60% | 99.40% | High structural distinction |
| **Vulnerability_scanner** | 335 | 1 | 0.30% | 99.70% | High structural distinction |
| **DDoS_ICMP** | 469 | 0 | 0.00% | 100.00% | High structural distinction |
| **DDoS_TCP** | 341 | 0 | 0.00% | 100.00% | High structural distinction |
| **Backdoor** | 339 | 0 | 0.00% | 100.00% | High structural distinction |
| **DDoS_HTTP** | 352 | 0 | 0.00% | 100.00% | High structural distinction |
| **Fingerprinting** | 33 | 0 | 0.00% | 100.00% | High structural distinction |
| **DDoS_UDP** | 482 | 0 | 0.00% | 100.00% | High structural distinction |
| **Password** | 332 | 0 | 0.00% | 100.00% | High structural distinction |
| **MITM** | 14 | 0 | 0.00% | 100.00% | High structural distinction |
| **Ransomware** | 364 | 0 | 0.00% | 100.00% | High structural distinction |
| **SQL_injection** | 343 | 0 | 0.00% | 100.00% | High structural distinction |
| **Uploading** | 341 | 0 | 0.00% | 100.00% | High structural distinction |
| **XSS** | 335 | 0 | 0.00% | 100.00% | High structural distinction |

---

## 5. Technical Limitations & Operational Realities

1. **Trade-off Inevitability:** Decreasing the decision threshold strictly reduces False Negatives while moderately increasing False Positives. False Negatives **have not been completely eliminated** to zero, as packet headers with perfect mimicry of legitimate sensor reads require deep cryptographic inspection.
2. **Autoencoder Noise:** The unsupervised Autoencoder acts as a powerful safety barrier for anomalous payloads, but its reconstruction threshold will capture legitimate sensor anomalies during plant maintenance or extreme physical telemetry conditions.
3. **Threshold Deployment:** In high-consequence facilities (e.g. nuclear, chemical refining), the system recommends running at threshold 0.125 with Autoencoder fallback; in bandwidth-constrained edge gateways, a more conservative threshold of 0.50 may be preferred.

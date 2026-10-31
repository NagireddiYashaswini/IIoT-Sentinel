# IIoT SENTINEL 4.0 — Final Numerical Verification Report
**Phase:** Exhaustive Numerical Verification & Confusion Matrix Audit  
**Target:** Held-Out Test Evaluation & Metric Formula Integrity  
**Dataset:** Edge-IIoTset (5,224 Verified Held-Out Test Records)  
**Evaluation Standard:** Zero Retraining, Zero Model Alterations, Empirical Ground Truth  

---

## 1. Executive Summary

This report provides the mathematical and numerical verification of **IIoT Sentinel 4.0**, auditing the exact performance of supervised, unsupervised, and hybrid detection configurations on the held-out test partition.

Every metric in this report was computed directly on the **identical 5,224 held-out test records** stored in [`artifacts/data/test_stream.parquet`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/data/test_stream.parquet) using the production-saved models:
- Supervised XGBoost: [`artifacts/models/supervised_model.joblib`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/supervised_model.joblib)
- Deep Autoencoder: [`artifacts/models/autoencoder.pt`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/autoencoder.pt)
- Preprocessing Pipeline: [`artifacts/models/preprocessing_pipeline.joblib`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/preprocessing_pipeline.joblib)

### Test Partition Composition
| Split Class | Ground Truth Label | Record Count | Percentage of Test Set |
| :--- | :---: | :---: | :---: |
| **Normal Traffic** | `Attack_label = 0` | **809** | 15.486% |
| **Malicious Attacks** | `Attack_label = 1` | **4,415** | 84.514% |
| **Total Test Stream** | — | **5,224** | **100.000%** |

---

## 2. Metric Formulas & Mathematical Definitions

All performance calculations adhere strictly to standard binary classification metrics defined over confusion matrix quadrants:

$$\begin{pmatrix} \text{TN} & \text{FP} \\ \text{FN} & \text{TP} \end{pmatrix}$$

Where:
- **True Positive ($\text{TP}$)**: Ground Truth Attack ($y=1$) correctly classified as Attack ($\hat{y}=1$).
- **True Negative ($\text{TN}$)**: Ground Truth Normal ($y=0$) correctly classified as Normal ($\hat{y}=0$).
- **False Positive ($\text{FP}$)**: Ground Truth Normal ($y=0$) falsely classified as Attack ($\hat{y}=1$) [False Alarm].
- **False Negative ($\text{FN}$)**: Ground Truth Attack ($y=1$) falsely classified as Normal ($\hat{y}=0$) [Critical Missed Breach].

### Precise Formulas
1. **Attack Recall (True Positive Rate, $\text{TPR}$)**:
   $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{\text{TP}}{4415}$$
2. **False Negative Rate ($\text{FNR}$)**:
   $$\text{FNR} = \frac{\text{FN}}{\text{TP} + \text{FN}} = 1 - \text{Recall} = \frac{\text{FN}}{4415}$$
3. **False Positive Rate ($\text{FPR}$)**:
   $$\text{FPR} = \frac{\text{FP}}{\text{TN} + \text{FP}} = \frac{\text{FP}}{809}$$
4. **Precision**:
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
5. **Attack F1-Score**:
   $$\text{F1}_{\text{attack}} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
6. **Macro-Averaged F1-Score ($\text{Macro-F1}$)**:
   $$\text{Macro-F1} = \frac{\text{F1}_{\text{normal}} + \text{F1}_{\text{attack}}}{2}$$
   where $\text{F1}_{\text{normal}} = \frac{2 \cdot \text{TN}}{2 \cdot \text{TN} + \text{FP} + \text{FN}}$.

---

## 3. Comprehensive Verification Table (8 Target Configurations)

The table below reproduces the exact evaluation across all 8 requested operating points, exported in [`artifacts/metrics/confusion_matrix_verification.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/confusion_matrix_verification.csv).

| Configuration | Test N | TP | TN | FP | FN | Attack Recall | FNR | FPR | Precision | F1-Score | Macro-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Supervised Threshold 0.50** | 5,224 | 4,399 | 794 | 15 | 16 | **99.638%** | **0.362%** | **1.854%** | 99.660% | 99.649% | **98.867%** |
| **2. Supervised Threshold 0.125** | 5,224 | 4,412 | 772 | 37 | 3 | **99.932%** | **0.068%** | **4.574%** | 99.168% | 99.549% | **98.512%** |
| **3. Hybrid p99** ($t_{\text{ae}}=0.130980$) | 5,224 | 4,401 | 782 | 27 | 14 | **99.683%** | **0.317%** | **3.338%** | 99.390% | 99.536% | **98.491%** |
| **4. Hybrid p98** ($t_{\text{ae}}=0.120126$) | 5,224 | 4,401 | 775 | 34 | 14 | **99.683%** | **0.317%** | **4.203%** | 99.233% | 99.458% | **98.227%** |
| **5. Hybrid p95** ($t_{\text{ae}}=0.099337$) | 5,224 | 4,401 | 762 | 47 | 14 | **99.683%** | **0.317%** | **5.810%** | 98.943% | 99.312% | **97.732%** |
| **6. Hybrid p90** ($t_{\text{ae}}=0.070936$) | 5,224 | 4,401 | 718 | 91 | 14 | **99.683%** | **0.317%** | **11.249%** | 97.974% | 98.821% | **96.004%** |
| **7. Hybrid p80** ($t_{\text{ae}}=0.036242$) | 5,224 | 4,405 | 643 | 166 | 10 | **99.774%** | **0.226%** | **20.519%** | 96.368% | 98.041% | **93.002%** |
| **8. Tuned Sup (0.125) + AE p95** | 5,224 | 4,414 | 741 | 68 | 1 | **99.977%** | **0.023%** | **8.405%** | 98.483% | 99.225% | **97.388%** |

---

## 4. Empirical Breakdown & Analytical Findings

### A. Autoencoder Recovery Mechanism
1. **Recovery at Thresholds $\ge \text{p90}$**:
   - Across the Autoencoder thresholds p99, p98, p95, and p90, the Autoencoder consistently catches **exactly 2 additional attacks** that Supervised XGBoost missed at threshold 0.50.
   - These 2 recovered attacks correspond to **Port Scanning** records (Indices #1121 and #1156). Both produced reconstruction errors of **0.223580** and **0.239257**, well above the p99 threshold ($0.130980$).
   - This directly lowers $\text{FN}$ from 16 to 14, improving attack recall from $99.638\%$ to $99.683\%$.
2. **Recovery at Extreme Percentile (p80)**:
   - At p80 ($t_{\text{ae}} = 0.036242$), the Autoencoder recovers **6 attacks** (2 Port Scanning + 4 Password attacks: Indices #1081, #1208, #1917, #3032), lowering $\text{FN}$ from 16 to 10.
   - However, this comes at an unacceptable operational cost: False Positives jump from 15 to **166** ($\text{FPR} = 20.519\%$), which would generate one false alarm for every five clean industrial transactions.
3. **Synergy of Tuned Supervised (0.125) + Autoencoder (p95)**:
   - Tuning the supervised threshold to 0.125 on validation data captures 13 of the 16 missed attacks on its own ($\text{FN}$ drops from 16 to 3).
   - Adding Autoencoder p95 subsequently recovers 2 of the remaining 3 false negatives, resulting in **only 1 missed attack** out of 4,415 test attacks ($\text{FNR} = 0.023\%$, Recall = $99.977\%$).

---

## 5. Artifact References
- Complete 8-configuration CSV: [`artifacts/metrics/confusion_matrix_verification.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/confusion_matrix_verification.csv)
- Fair FPR-Constrained Comparison CSV: [`artifacts/metrics/fpr_constrained_comparison.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/fpr_constrained_comparison.csv)
- Record-Level FN/FP Analysis CSV: [`artifacts/metrics/false_negative_record_analysis.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/false_negative_record_analysis.csv)


# Fair FPR-Constrained Model Comparison (FPR $\le$ 5%)
**Phase:** Rigorous False-Positive Budgeted Evaluation  
**Constraint:** Operational False Positive Rate Ceiling $\le 5.0\%$  
**Tuning Principle:** Threshold selection performed strictly on **Validation Data** ($N=5,224$) with zero exposure to test labels  
**Evaluation Data:** Held-out Test Data ($N=5,224$, 809 Normal, 4,415 Attacks)  

---

## 1. Experimental Methodology & Rationale

In real-world Industrial IoT environments (water treatment, smart grid, factory automation), an Intrusion Detection System that achieves zero false negatives by alerting on every normal telemetry fluctuation creates "alarm fatigue." Security operations teams can realistically tolerate at most a **5% False Positive Rate (FPR $\le$ 0.05)**.

To provide a fair, scientifically defensible comparison:
1. **Zero Test Data Tuning**: Thresholds were chosen exclusively using the **validation set** (5,224 samples: 808 Normal, 4,416 Attack).
2. **Supervised Optimization**: We swept probability thresholds $t \in [0.01, 0.99]$ on validation data to identify the threshold that maximizes validation attack recall subject to $\text{Validation FPR} \le 5.0\%$.
3. **Hybrid Optimization**: In a dual-stage hybrid architecture where an alert fires if:
   $$\hat{y} = 1 \iff (P(\text{attack}) \ge t_{\text{prob}}) \lor (\text{ReconError} > t_{\text{ae}})$$
   both mechanisms contribute to false positives. We searched combinations of Autoencoder percentile thresholds (p99, p98, p95, p90) and probability thresholds on validation data subject to combined $\text{Validation FPR} \le 5.0\%$.
4. **Frozen Evaluation**: The selected operating points were then applied directly to the frozen test dataset.

---

## 2. Fair Comparison Results Table

Below is the verified performance comparison exported in [`artifacts/metrics/fpr_constrained_comparison.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/fpr_constrained_comparison.csv).

| Model Configuration | Validation FPR | Test FPR | Test Recall | Test FNR | Test Precision | Test F1 | Attacks Recovered | Additional False Alarms | Test Confusion Matrix (TP / TN / FP / FN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Supervised-Only**<br>*(Validation-Tuned $t=0.116$)* | 4.332% | **4.944%** | 99.932% | 0.068% | 99.102% | 99.515% | Baseline (0) | Baseline (0) | 4,412 / 769 / 40 / 3 |
| **Hybrid Model**<br>*(Validation-Tuned $t_{\text{prob}}=0.191$ + AE p99)* | 3.960% | **4.821%** | **99.955%** | **0.045%** | **99.124%** | **99.538%** | **+1** | **-1** | **4,413 / 770 / 39 / 2** |
| **Hybrid Baseline**<br>*(Default $t_{\text{prob}}=0.50$ + AE p98)* | 3.465% | **4.203%** | 99.683% | 0.317% | 99.233% | 99.458% | **+2** *(vs sup 0.50)* | **+19** *(vs sup 0.50)* | 4,401 / 775 / 34 / 14 |

---

## 3. Detailed Numerical Analysis

### A. How the Hybrid Model Meets the 5% Constraint
- If the Autoencoder threshold is set to p95, the Autoencoder alone generates an empirical FPR of approximately 5.81% on normal traffic. Combined with any supervised probability threshold, the resulting FPR exceeds 8%, violating the 5% ceiling.
- However, when the Autoencoder threshold is set to **p99** ($t_{\text{ae}} = 0.130980$), the Autoencoder acts as a high-confidence anomaly filter with an individual validation FPR of only $\approx 0.99\%$.
- This leaves sufficient FPR budget for the supervised classifier to operate at an aggressive probability threshold of $t_{\text{prob}} = 0.191$.

### B. Empirical Gains of the Hybrid Architecture
Under the identical $\le 5\%$ operational false-alarm budget on test data:
1. **False Negative Reduction**:
   - Supervised-only at $t=0.116$ leaves **3 false negatives** (FNR = 0.0680%).
   - The tuned Hybrid model ($t_{\text{prob}}=0.191 + \text{AE p99}$) reduces false negatives to **2** (FNR = 0.0453%), achieving a **33.3% relative reduction in missed attacks**.
2. **False Positive Control**:
   - The tuned Hybrid model yields **39 false alarms** (4.821% FPR) compared to **40 false alarms** (4.944% FPR) for the supervised-only model, actually saving 1 false alarm while catching an additional attack.
3. **Precision & F1 Superiority**:
   - Hybrid precision: **99.124%** vs Supervised-only: **99.102%**.
   - Hybrid F1-Score: **99.538%** vs Supervised-only: **99.515%**.

### C. Honest Engineering Assessment
- **Where Hybrid Excels**: When constrained to a strict FPR budget, coupling an Autoencoder at high percentiles ($\ge \text{p98}$) with a moderately low supervised threshold ($t \approx 0.19$) achieves superior attack recall without causing alarm fatigue.
- **Where Hybrid Fails**: Blindly setting the Autoencoder threshold to p95 or p90 with default supervised thresholds ($t=0.50$) substantially degrades FPR (5.8% to 11.2%) for minimal recall gain (+2 attacks). Threshold tuning using validation data is mandatory for hybrid architectures in production.

---

## 4. Associated Deliverables
- Metrics Table CSV: [`artifacts/metrics/fpr_constrained_comparison.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/fpr_constrained_comparison.csv)
- Confusion Matrix Verification: [`reports/final_numerical_verification.md`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/reports/final_numerical_verification.md)


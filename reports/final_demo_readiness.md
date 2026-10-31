# IIoT SENTINEL 4.0 — Final Demo Readiness & Code-Level Audit Report
**Audit Date:** 2026-10-31  
**Project:** IIoT Sentinel 4.0 — Hybrid AI-Based Industrial IoT Intrusion Detection System  
**Audit Standard:** Strict Code-Level Execution, Zero Fabrication, Frozen Architecture  
**Streamlit Status:** Live & Serving at `http://localhost:8501` (HTTP 200 OK)  
**Test Suite Status:** 19/19 Unit & Integration Tests Passed  

---

## 1. Hybrid Decision Logic & Code References

The fusion of supervised classification and unsupervised Autoencoder anomaly detection is implemented in [`src/hybrid_detector.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py) through the `HybridDecisionEngine` class.

### A. Architectural Workflow & Mathematical Mechanics
For each incoming preprocessed network record $x$:
1. **Supervised Binary Classifier**:
   $$P_{\text{attack}}(x) = \text{predict\_proba}(x)[:, 1], \quad \hat{y}_{\text{sup}} = \mathbb{I}(P_{\text{attack}}(x) \ge t_{\text{prob}})$$
   *(Code: [`src/hybrid_detector.py#L69-L74`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L69-L74))*
2. **Deep Autoencoder Anomaly Detector**:
   $$e_{\text{recon}}(x) = \frac{1}{D} \sum_{j=1}^D (x_j - \hat{x}_j)^2, \quad \hat{y}_{\text{ae}} = \mathbb{I}(e_{\text{recon}}(x) > t_{\text{ae}})$$
   *(Code: [`src/hybrid_detector.py#L83-L84`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L83-L84))*
3. **Supervised Multiclass Classifier**:
   Assigns attack taxonomy and confidence $C_{\text{mc}}(x)$ if a signature matches known exploits.  
   *(Code: [`src/hybrid_detector.py#L77-L80`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L77-L80))*

### B. 4-Case Triage Logic Table
*(Code: [`src/hybrid_detector.py#L99-L129`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L99-L129))*

| Case # | Decision Label | Severity | Trigger Conditions | Operational Security Action |
| :---: | :--- | :--- | :--- | :--- |
| **Case 1** | **`NORMAL`** | `GREEN (NORMAL)` | $\hat{y}_{\text{sup}} = 0 \;\land\; e_{\text{recon}} \le t_{\text{ae}} \;\land\; \neg \text{Uncertain}$ | Clean telemetry stream; routed to PLCs/SCADA without delay. |
| **Case 2** | **`KNOWN ATTACK`** | `RED (CRITICAL)` | $\hat{y}_{\text{sup}} = 1$ | Automated gateway firewall drops packet; isolates specific attack taxonomy. |
| **Case 3** | **`POTENTIAL UNKNOWN ATTACK`** | `AMBER (WARNING)` | $\hat{y}_{\text{sup}} = 0 \;\land\; \hat{y}_{\text{ae}} = 1$ | Out-of-distribution anomaly bypasses supervised model; flagged for forensic analysis. |
| **Case 4** | **`SUSPICIOUS / UNCERTAIN`** | `AMBER (WARNING)` | $|P_{\text{attack}} - t_{\text{prob}}| \le \delta \;\land\; e_{\text{recon}} > 0.8 \cdot t_{\text{ae}}$ | Ambiguous classifier boundary with elevated reconstruction variance; analyst triage. |

### C. Verification: Conversion of Normal to Attack
In [`src/hybrid_detector.py#L151-L155`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L151-L155):
```python
# Operational Hybrid Flag: Treat KNOWN ATTACK, POTENTIAL UNKNOWN ATTACK, and SUSPICIOUS as flagged security events
hybrid_flags = df_decisions["hybrid_decision"].apply(
    lambda d: 0 if d == "NORMAL" else 1
).to_numpy()
```
When the supervised model predicts Normal ($\hat{y}_{\text{sup}} = 0$), but the Autoencoder detects an anomaly ($\hat{y}_{\text{ae}} = 1$), the decision is assigned either `POTENTIAL UNKNOWN ATTACK` (Case 3) or `SUSPICIOUS / UNCERTAIN` (Case 4). Both map to **`1` (Security Alert)**, converting a false negative into a detected security event.

**Empirical Proof on Test Data**:
In [`artifacts/metrics/false_negative_record_analysis.csv`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/false_negative_record_analysis.csv):
- Record **#1121** (Port_Scanning): $P_{\text{attack}} = 0.1001$ (Supervised = 0), $e_{\text{recon}} = 0.223580 > t_{\text{ae}}$ ($0.099337$) $\rightarrow$ **Recovered to Detected Anomaly Alert**.
- Record **#1156** (Port_Scanning): $P_{\text{attack}} = 0.0970$ (Supervised = 0), $e_{\text{recon}} = 0.239257 > t_{\text{ae}}$ ($0.099337$) $\rightarrow$ **Recovered to Detected Anomaly Alert**.

---

## 2. Dashboard-to-Artifact Consistency Audit

The Streamlit dashboard (`app.py`) was audited for end-to-end consistency with the serialized model artifacts and verified metrics.

### A. Loaded Artifacts & Integrity Checks
| Component | On-Disk File Source | Size / Metadata | Verification Status |
| :--- | :--- | :--- | :---: |
| **Supervised Classifier** | [`artifacts/models/supervised_model.joblib`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/supervised_model.joblib) | 231 KB (XGBoost, 100 estimators, max_depth=8) | **PASS** |
| **Multiclass Classifier** | [`artifacts/models/multiclass_model.joblib`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/multiclass_model.joblib) | 14.5 MB (15-class taxonomy) | **PASS** |
| **Preprocessing Pipeline** | [`artifacts/models/preprocessing_pipeline.joblib`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/preprocessing_pipeline.joblib) | 5.4 KB (StandardScaler + OneHotEncoder) | **PASS** |
| **Deep Autoencoder** | [`artifacts/models/autoencoder.pt`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/models/autoencoder.pt) | 92.5 KB (5-layer PyTorch weights) | **PASS** |
| **AE Anomaly Thresholds** | [`artifacts/autoencoder/thresholds.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/autoencoder/thresholds.json) | p90=0.0709, p95=0.0993, p98=0.1201, p99=0.1310 | **PASS** |
| **Run Manifest** | [`artifacts/run_manifest.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/run_manifest.json) | Seed=42, Features=39, Mode=FAST | **PASS** |
| **Test Stream Stream** | [`artifacts/data/test_stream.parquet`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/data/test_stream.parquet) | 5,224 rows, 68 columns | **PASS** |

### B. Metric Alignment with Verified Test Dataset (5,224 Records)
All figures displayed in the dashboard originate directly from [`artifacts/metrics/hybrid_metrics.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/hybrid_metrics.json) and [`artifacts/data/test_stream.parquet`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/data/test_stream.parquet):
- **Total Test Records**: **5,224**
- **Ground-Truth Attacks**: **4,415**
- **Ground-Truth Normal**: **809**
- **Confusion Matrix in `hybrid_metrics.json`**:
  - True Positives ($\text{TP}$): **4,414**
  - True Negatives ($\text{TN}$): **704**
  - False Positives ($\text{FP}$): **105**
  - False Negatives ($\text{FN}$): **1**
  - Attack Recall: **99.977%** ($\frac{4414}{4415}$)
  - False Negative Rate: **0.023%** ($\frac{1}{4415}$)
- **Decision Category Breakdown**:
  - `KNOWN ATTACK`: 4,449
  - `NORMAL`: 705
  - `SUSPICIOUS / UNCERTAIN`: 70
  - Sum: $4,449 + 705 + 70 = \mathbf{5,224}$ records.

### C. Streamlit AppTest Multi-Page Verification
Every page was tested programmatically using `streamlit.testing.v1.AppTest`:
- `🛡️ Security Overview`: **0 Exceptions**
- `📡 Simulated Traffic Monitoring`: **0 Exceptions**
- `📊 Attack Analytics`: **0 Exceptions**
- `🎯 False Negative Analysis`: **0 Exceptions**
- `🧠 Autoencoder Anomaly Monitoring`: **0 Exceptions**
- `🔍 AI Explainability`: **0 Exceptions**
- `📤 Test with New Data`: **0 Exceptions**
- `🚨 Security Alert History`: **0 Exceptions**
- `⚡ Model Performance`: **0 Exceptions**

---

## 3. Unseen-Attack Experiment Isolation Audit

The script [`scripts/unseen_attack_experiment.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/scripts/unseen_attack_experiment.py) was audited for strict scientific isolation:

1. **Held-Out Attack Classes**: `Fingerprinting` (33 test records) and `MITM` (14 test records) were completely excluded from the supervised training set.
2. **Preprocessing Isolation**: `train_df_filtered` (24,157 rows) was filtered **prior** to calling `preprocessor.fit()`. Imputer medians and scaler parameters were computed with zero exposure to held-out attack samples.
3. **Threshold Selection Isolation**: Autoencoder anomaly thresholds were computed strictly from legitimate normal validation traffic ($N=808$). Held-out attack labels were never used for model or threshold selection.
4. **Data Overlap**:
   - $\text{Train} \cap \text{Val} = 0$, $\text{Train} \cap \text{Test} = 0$, $\text{Val} \cap \text{Test} = 0$.
   - Cross-split duplicate records = **0**.
5. **Results**:
   - Supervised XGBoost detected 90.9% of Fingerprinting and 100% of MITM via protocol-level feature generalization (SYN rates, payload sizes).
   - Autoencoder flagged 51.5% of Fingerprinting and 85.7% of MITM as structural anomalies without any label exposure.

---

## 4. Test Suite Execution Results

All 19 tests across the test suite were executed via `python -m pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Sridevinivas\Documents\IIoT-Sentinel-4.0
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.12.1, langsmith-0.6.0
collected 19 items

tests\test_autoencoder.py ..                                             [ 10%]
tests\test_external_uploads_validation.py .......                        [ 47%]
tests\test_new_data_upload.py ...                                        [ 63%]
tests\test_no_leakage.py ....                                            [ 84%]
tests\test_pipeline_smoke.py ...                                         [100%]

======================= 19 passed, 1 warning in 18.63s ========================
```

---

## 5. Live Application Status

The Streamlit web application is actively running:
- **Process Mode**: Background Daemon Process
- **Network Port**: `8501`
- **Probe Verification**: `GET http://localhost:8501` returned **HTTP 200 OK**
- **Dashboard Access**: [`http://localhost:8501`](http://localhost:8501)

---

## 6. Audit Observations & Remaining Technical Realities

1. **Uncertainty Margin Interaction with Low Supervised Thresholds**:
   - In [`src/hybrid_detector.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py), when $t_{\text{prob}} = 0.125$ and `uncertainty_margin` = $0.15$, the lower bound $(0.125 - 0.15 = -0.025)$ encompasses small probabilities.
   - Consequently, normal packets with elevated reconstruction error are categorized as `SUSPICIOUS / UNCERTAIN` (Amber warning) rather than `POTENTIAL UNKNOWN ATTACK`. Functionally, both trigger security alerts and analyst triage, maintaining correct operational security posture.
2. **Report Presentation**:
   - The markdown reports in [`reports/`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/reports) exist as persistent audit documentation in the repository. The Streamlit dashboard visualizes the corresponding structured JSON and Parquet metrics directly through interactive Plotly dashboards rather than embedding raw markdown files.
3. **Architecture Stability**:
   - The verified test results (5,224 records), model weights, thresholds, and preprocessors remain unaltered, fully reproducible, and demo-ready.


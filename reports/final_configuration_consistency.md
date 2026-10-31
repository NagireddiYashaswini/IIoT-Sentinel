# IIoT SENTINEL 4.0 — Final Configuration Consistency Report
**Phase:** Primary Dashboard Operating Configuration Standardization  
**Standard:** Validation-Tuned FPR-Constrained Configuration ($\text{FPR} \le 5.0\%$)  
**Operating Parameters:** $t_{\text{prob}} = 0.190741$, $t_{\text{ae}} = 0.130980$ (p99)  
**Evaluated Data:** Frozen Edge-IIoTset Test Stream ($N=5,224$: 4,415 Attacks, 809 Normal)  
**Verification Status:** 100% Artifact-to-Dashboard Consistency, 19/19 Pytest Passed, 9/9 AppTest Passed, Live HTTP 200  

---

## 1. Executive Summary & Rationale

A configuration mismatch was previously identified between the fair $\text{FPR} \le 5.0\%$ validation experiment and the primary operating configuration displayed in the Streamlit dashboard:

- **Previous Dashboard Configuration**: Loaded $t_{\text{prob}} = 0.125$ and $t_{\text{ae}} = 0.099337$ (p95). While this configuration maximized raw attack recovery ($\text{FN}=1$), it incurred 105 False Positives ($\text{FPR} = 12.98\%$), exceeding the operational false alarm tolerance required for real-world Industrial IoT control networks.
- **Corrected Standard Operating Configuration**: The dashboard, run manifest, serialized metrics, and test stream have been synchronized to the **validation-tuned hybrid configuration**:
  - Supervised Probability Threshold: **`0.190741`**
  - Autoencoder Anomaly Threshold: **`0.130980` (p99.0)**
  - Test True Positives ($\text{TP}$): **`4,413`**
  - Test True Negatives ($\text{TN}$): **`770`**
  - Test False Positives ($\text{FP}$): **`39`**
  - Test False Negatives ($\text{FN}$): **`2`**
  - Test False Positive Rate ($\text{FPR}$): **`4.821%`** ($\le 5.0\%$ constraint satisfied)
  - Test Attack Recall: **`99.955%`**
  - Test Precision: **`99.124%`**
  - Test F1-Score: **`99.538%`**
  - Test Macro-F1: **`98.472%`**

Every single metric, card, confusion matrix, and alert counter across all 9 dashboard pages now reflects this exact, verified configuration without combining metrics from differing thresholds.

---

## 2. Location-by-Location Audit & Alignment Matrix

We audited every file in the codebase where thresholds are loaded, configured, or rendered:

| File / Component | Previous State | Corrected Operating State | Verification Status |
| :--- | :--- | :--- | :---: |
| [`artifacts/run_manifest.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/run_manifest.json) | $t_{\text{best}} = 0.125$, $t_{\text{ae}} = 0.099337$ (p95) | $t_{\text{best}} = \mathbf{0.190741}$, $t_{\text{ae}} = \mathbf{0.130980}$ (p99.0) | **PASS** |
| [`artifacts/metrics/hybrid_metrics.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/hybrid_metrics.json) | $\text{TP}=4414, \text{TN}=704, \text{FP}=105, \text{FN}=1$ | $\text{TP}=\mathbf{4413}, \text{TN}=\mathbf{770}, \text{FP}=\mathbf{39}, \text{FN}=\mathbf{2}$ | **PASS** |
| [`artifacts/metrics/autoencoder_metrics.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/autoencoder_metrics.json) | `selected_threshold`: 0.099337 (p95) | `selected_threshold`: $\mathbf{0.130980}$ (p99.0) | **PASS** |
| [`artifacts/metrics/metrics_summary.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/metrics_summary.json) | `best_threshold`: 0.125 | `best_threshold`: $\mathbf{0.190741}$ (validation-tuned) | **PASS** |
| [`artifacts/data/test_stream.parquet`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/data/test_stream.parquet) | `NORMAL`: 705, `KNOWN`: 4449, `SUSP`: 70 | `NORMAL`: $\mathbf{772}$, `KNOWN`: $\mathbf{4438}$, `UNKNOWN`: $\mathbf{10}$, `SUSP`: $\mathbf{4}$ | **PASS** |
| [`app.py#L168-L169`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/app.py#L168-L169) | Hardcoded `AE Threshold (p95)` | Dynamic `AE Threshold (p99.0): 0.1310` | **PASS** |
| [`dashboard/overview.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/overview.py) | Overview cards and pie chart | Aligned to 772 Normal, 4,438 Known, 10 Unknown, 4 Suspicious | **PASS** |
| [`dashboard/alerts.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/alerts.py) | 4,519 alerts; "Immediate Containment" | $\mathbf{4,452}$ alerts; $\mathbf{"Simulated Containment / Triage"}$ | **PASS** |
| [`dashboard/autoencoder_page.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/autoencoder_page.py) | Displayed p95 as only threshold | Active threshold: $\mathbf{0.130980}$ (p99.0); comparison: $0.099337$ (p95) | **PASS** |
| [`dashboard/model_performance.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/model_performance.py) | FPR 12.98% / F1 98.81% | Recall $\mathbf{99.955\%}$, FPR $\mathbf{4.821\%}$, Precision $\mathbf{99.124\%}$, F1 $\mathbf{99.538\%}$ | **PASS** |
| [`dashboard/false_negatives.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/false_negatives.py) | Selected threshold 0.125 | Selected threshold $\mathbf{0.191}$ (validation curve vline at 0.191) | **PASS** |
| [`dashboard/new_data.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/new_data.py) | Defaulted to 0.50 | Explicitly passes $t_{\text{prob}}=\mathbf{0.190741}, t_{\text{ae}}=\mathbf{0.130980}$ | **PASS** |

---

## 3. Preservation of p95 High-Sensitivity Configuration

To adhere to scientific thoroughness without mixing metrics:
1. **Serialized Preservation**: The previous p95 operating configuration is preserved under the key `"comparison_p95_configuration"` in [`artifacts/metrics/hybrid_metrics.json`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/artifacts/metrics/hybrid_metrics.json):
   ```json
   "comparison_p95_configuration": {
     "configured_binary_threshold": 0.125,
     "configured_ae_threshold": 0.099337,
     "configured_ae_percentile": "p95.0",
     "tp": 4414,
     "tn": 704,
     "fp": 105,
     "fn": 1,
     "attack_recall": 0.999773,
     "fnr": 0.000227,
     "fpr": 0.129790,
     "macro_f1": 0.959061,
     "note": "Optional high-sensitivity operating point (elevated false alarms: FPR 12.98%)"
   }
   ```
2. **Dashboard Side-by-Side Presentation**:
   - In [`dashboard/autoencoder_page.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/autoencoder_page.py), the headline metrics display:
     - **Active Threshold (p99.0)**: `0.130980` (Operational standard for $\text{FPR} \le 5\%$)
     - **Comparison Threshold (p95)**: `0.099337` (Optional higher-sensitivity baseline with elevated false alarms)

---

## 4. Remediation of Automated Gateway Claims

In accordance with Industry 4.0 and ICS cybersecurity realism guidelines:
- All claims of automated gateway isolation have been replaced with **simulated gateway isolation** or **analyst triage recommendations**:
  - In [`dashboard/alerts.py#L28`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/dashboard/alerts.py#L28): Replaced `delta="Immediate Containment"` with `delta="Simulated Containment / Triage"`.
  - In [`src/hybrid_detector.py#L113`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L113): Retained explicit simulated wording: `"Recommended simulated action: Gateway filter rule to isolate {atk_type} (Confidence: {mc_conf*100:.1f}%)."`.
  - In [`src/hybrid_detector.py#L128`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/src/hybrid_detector.py#L128): Retained explicit simulated wording: `"Simulated telemetry: Legitimate industrial sensor and protocol flow record within benign bounds."`.

---

## 5. Verification Test Suite & Live Streamlit Application Results

### A. Pytest Automated Test Suite
Executed `python -m pytest`:
- **Result**: **19 passed, 1 warning in 23.81s**
- Zero test regressions or contract violations.

### B. Streamlit Multi-Page AppTest
Executed programmatic UI testing across all 9 pages:
1. `🛡️ Security Overview`: **0 Exceptions**
2. `📡 Simulated Traffic Monitoring`: **0 Exceptions**
3. `📊 Attack Analytics`: **0 Exceptions**
4. `🎯 False Negative Analysis`: **0 Exceptions**
5. `🧠 Autoencoder Anomaly Monitoring`: **0 Exceptions**
6. `🔍 AI Explainability`: **0 Exceptions**
7. `📤 Test with New Data`: **0 Exceptions**
8. `🚨 Security Alert History`: **0 Exceptions**
9. `⚡ Model Performance`: **0 Exceptions**

### C. Live Server Verification
- Server Status: **Running as Daemon Process on Port 8501**
- Health Probe: `GET http://localhost:8501` returned **HTTP 200 OK**
- Browser Access URL: [`http://localhost:8501`](http://localhost:8501)


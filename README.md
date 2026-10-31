# IIoT SENTINEL 4.0 — Hybrid AI-Powered Industrial IoT Intrusion Detection System

**Author:** B.Tech Artificial Intelligence and Data Science Student  
**Project:** Industry 4.0 Capstone Engineering Group Project  
**Testbed Dataset:** Edge-IIoTset (Industrial IoT and Cyber-Physical System Testbed)  
**Status:** Complete, Verified, Fully Runnable  

---

## 1. Project Overview & Operational Objective

**IIoT SENTINEL 4.0** is an enterprise-grade industrial intrusion detection and anomaly monitoring software platform designed specifically for Industry 4.0 environments. It continuously inspects packet headers and telemetry flowing between industrial sensors (temperature, pressure, water level, sound, flame, pH, ultrasonic distance), Programmable Logic Controllers (PLCs), edge gateways, and Supervisory Control and Data Acquisition (SCADA) master units.

### Core Objectives Achieved:
1. **Normal vs. Malicious Identification:** Binary classification of telemetry streams.
2. **Taxonomic Threat Classification:** Multiclass attack classification across 14 discrete industrial cyberattack vectors (DDoS UDP/TCP/ICMP/HTTP, Industrial Ransomware, SQL Injection, XSS, Arbitrary Uploading, Backdoor Trojans, OS Fingerprinting, Vulnerability Scanning, MITM, Password Brute-force).
3. **Unsupervised Normal Telemetry Anomaly Detection:** PyTorch neural Autoencoder trained **strictly on normal telemetry**, establishing a mathematical baseline of legitimate industrial behavior.
4. **4-Case Hybrid Triage Matrix:** Fuses Supervised Machine Learning and Unsupervised Autoencoder error metrics to isolate:
   - `NORMAL`
   - `KNOWN ATTACK`
   - `POTENTIAL UNKNOWN ATTACK` (Unsupervised safety net for zero-day threats)
   - `SUSPICIOUS / UNCERTAIN` (Low-confidence boundary conditions)
5. **Empirical False-Negative Reduction:** Validation-based decision threshold optimization cuts undetected intrusions without dataset snooping.
6. **AI Explainability:** SHAP TreeExplainer for supervised model feature attribution; feature deviation error attribution for Autoencoder anomalies.
7. **External New Data Testing:** Dedicated upload console for un-trained CSV/XLSX captures with automatic schema validation and distribution drift warnings.
8. **Dark-Themed SOC Streamlit Dashboard:** 9 interactive pages featuring real-time simulated replay, attack profiling, and incident logs.

---

## 2. Master System Architecture

```
                       Industrial IoT Network Traffic
                                     │
                                     ▼
                      Data Ingestion / File Upload
                       (Edge-IIoTset / New Dataset)
                                     │
                                     ▼
                         Feature Schema Validation
                   (Missing/Extra Column Check & Drift)
                                     │
                                     ▼
                     Fitted Preprocessing Pipeline
                 (Median Imputation + Robust Scaling)
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
       Supervised ML Model                     Deep Autoencoder
       (XGBoost / Random Forest)              (PyTorch 5-Layer Dense)
                 │                                       │
                 ▼                                       ▼
      Binary Attack Probability               Reconstruction Error
      & Multiclass Taxonomy MSE                Calculation: ||x - x̂||²
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                          Hybrid Decision Engine
                         (Configurable 4-Way Triage)
                                     │
        ┌───────────────┬────────────┴──────────────┬──────────────────┐
        ▼               ▼                           ▼                  ▼
     Case 1          Case 2                      Case 3             Case 4
     NORMAL       KNOWN ATTACK         POTENTIAL UNKNOWN ATTACK   SUSPICIOUS / UNCERTAIN
  (P < Thresh &  (P >= Thresh)           (P < Thresh & Error >     (Boundary P & Elevated
   Error <= AE)  [Multiclass Identifies        AE_Thresh)                 Error)
                  Attack Vector]
                                     │
                                     ▼
                           SHAP Explainability
                  (Global & Per-Record Root-Cause Attributions)
                                     │
                                     ▼
                        Security Operations Alerts
                                     │
                                     ▼
                         Streamlit SOC Dashboard
```

---

## 3. How a New Network Traffic Packet Moves Through the System

1. **Ingestion & Feature Alignment:** The packet's raw protocol fields enter the system. High-cardinality IP addresses, MAC addresses, timestamps, client hostnames, and arbitrary payload blobs are stripped away to prevent spatial/temporal leakage.
2. **Transformation:** The remaining 39 behavioral protocol fields (TCP flags, sequence metrics, port IDs, ICMP checksums, MQTT telemetry headers) are transformed using the saved `IIoTPreprocessor` fitted strictly on training data.
3. **Parallel Inference:**
   - **Branch A (Supervised Model):** The tuned XGBoost model estimates the probability that the packet matches known attack signatures ($P(\text{Attack})$) and runs multiclass classification.
   - **Branch B (Autoencoder):** The PyTorch Autoencoder attempts to compress and reconstruct the packet. The Mean Squared Error (MSE) between original features and reconstructed features is computed.
4. **Hybrid Decision Fusion:**
   - If $P(\text{Attack}) \ge \text{Threshold}$ $\rightarrow$ **`KNOWN ATTACK`** (Immediate containment rule).
   - If $P(\text{Attack}) < \text{Threshold}$ AND $\text{MSE} \le \text{AE\_Threshold}$ $\rightarrow$ **`NORMAL`** (Permitted through edge gateway).
   - If $P(\text{Attack}) < \text{Threshold}$ BUT $\text{MSE} > \text{AE\_Threshold}$ $\rightarrow$ **`POTENTIAL UNKNOWN ATTACK`** (Autoencoder caught structural abnormality; forwarded to Tier-2 SOC analysts).
   - If $P(\text{Attack})$ is near the decision boundary AND reconstruction error is elevated $\rightarrow$ **`SUSPICIOUS / UNCERTAIN`** (Flagged for triage).
5. **Attribution & Alerting:** SHAP calculates which specific packet headers drove the classification, and the incident is displayed in the Streamlit SOC console.

---

## 4. Technology Stack

- **Core Runtime:** Python 3.10+ / 3.13 (Windows-compatible)
- **Data Engineering:** Pandas, NumPy, PyArrow, OpenPyXL
- **Supervised Machine Learning:** Scikit-learn, XGBoost, Imbalanced-learn (SMOTE)
- **Deep Learning Anomaly Detection:** PyTorch (`torch.nn`)
- **Explainable AI (XAI):** SHAP (`shap.TreeExplainer`)
- **Interactive SOC Dashboard:** Streamlit, Plotly Express & Graph Objects
- **Testing & Quality Assurance:** Pytest

---

## 5. Directory Structure

```
IIoT-Sentinel-4.0/
├── Edge-IIoTset dataset/
│   ├── Attack traffic/                     # Raw attack captures (.csv & .pcap)
│   ├── Normal traffic/                     # Raw sensor captures (.csv & .pcap)
│   └── Selected dataset for ML and DL/
│       ├── ML-EdgeIIoT-dataset.csv         # Primary benchmark (157,800 rows, 63 cols)
│       └── DNN-EdgeIIoT-dataset.csv        # Scaled deep learning benchmark (1.16 GB)
│
├── config.py                               # System configurations, paths, hyperparams
├── utils.py                                # Safe JSON serialization (NaN-safe), timers, metrics
├── requirements.txt                        # Pinned dependencies
├── README.md                               # Presentation-ready documentation
├── pytest.ini                              # Test configuration
│
├── .streamlit/
│   ├── config.toml                         # Industrial dark theme configuration
│   └── credentials.toml                    # Local headless credentials
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py                      # Data loader supporting CSV/XLSX with stratified sampling
│   ├── demo_data.py                        # Synthetic IIoT telemetry generator for demo mode
│   ├── preprocessing.py                    # Serializable leakage-free IIoTPreprocessor
│   ├── features.py                         # Schema validation & Kolmogorov-Smirnov drift detection
│   ├── imbalance.py                        # Class weighting, SMOTE, validation threshold tuning
│   ├── models.py                           # Binary & multiclass classifier training & benchmarking
│   ├── autoencoder.py                      # Normal-only PyTorch Autoencoder anomaly detector
│   ├── hybrid_detector.py                  # 4-case hybrid decision fusion engine
│   ├── evaluate.py                         # Rigorous 3-way evaluation on identical held-out test data
│   ├── explain.py                          # SHAP TreeExplainer & Autoencoder error attribution
│   ├── cross_dataset.py                    # Optional ToN-IoT cross-dataset evaluation
│   ├── export_artifacts.py                 # Persists models, metrics, parquets, run manifest
│   └── validate_artifacts.py               # Comprehensive integrity validator (22 required files)
│
├── dashboard/
│   ├── overview.py                         # Page 1: Security Overview
│   ├── monitoring.py                       # Page 2: Simulated Traffic Monitoring
│   ├── analytics.py                        # Page 3: Attack Analytics
│   ├── false_negatives.py                  # Page 4: False Negative Analysis
│   ├── autoencoder_page.py                 # Page 5: Autoencoder Anomaly Monitoring
│   ├── explainability.py                   # Page 6: AI Explainability (SHAP)
│   ├── new_data.py                         # Page 7: Test with New Data
│   ├── alerts.py                           # Page 8: Security Alert History
│   └── model_performance.py                # Page 9: Model Performance
│
├── artifacts/
│   ├── models/                             # Saved models (.joblib, .pt, feature_columns.json)
│   ├── metrics/                            # Metrics summaries, confusion matrices
│   ├── explain/                            # SHAP global/local arrays & .npz bundles
│   ├── data/                               # Parquet test replay streams, class distributions
│   ├── autoencoder/                        # Reconstruction thresholds & error parquets
│   └── run_manifest.json                   # Verified training run metadata
│
├── reports/
│   ├── dataset_inspection_report.md        # Initial dataset audit & column categorization
│   ├── false_negative_analysis.md          # Sensitivity tuning & missed threat breakdown
│   ├── hybrid_model_comparison.md          # 3-way comparative evaluation report
│   └── results_summary.md                  # Executive run summary
│
├── tests/
│   ├── test_pipeline_smoke.py              # Smoke tests for data generation and pipeline
│   ├── test_no_leakage.py                  # Data leakage & partition isolation tests
│   ├── test_autoencoder.py                 # Autoencoder normal-only convergence tests
│   └── test_new_data_upload.py             # Schema validation and shift warning tests
│
└── data/
    ├── test_samples/                       # Sample CSV files for testing upload page
    └── raw/ton_iot/                        # Optional ToN-IoT directory
```

---

## 6. Exact Execution & Installation Commands

### 6.1 Installation
Install dependencies into your Python virtual environment:
```powershell
pip install -r requirements.txt
```

### 6.2 Running Unit Tests
Execute the test suite to verify pipeline integrity:
```powershell
python -m pytest
```

### 6.3 Pipeline Training Commands

#### Option A: Fast Training on Actual Edge-IIoTset (Recommended)
Executes stratified sampling across all 15 classes from the actual dataset:
```powershell
python train.py --fast
```

#### Option B: Offline Synthetic Demo Mode
Runs the complete pipeline in demo mode using synthetic IIoT telemetry:
```powershell
python train.py --demo
```

#### Option C: Full Dataset Training
Trains on all 157,800 records from `ML-EdgeIIoT-dataset.csv`:
```powershell
python train.py --full
```

### 6.4 Launching the Streamlit SOC Dashboard
Launch the multi-page dashboard:
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 7. Measured Empirical Performance (Held-Out Test Set)

| Metric | Supervised Only (XGBoost) | Deep Autoencoder Only (Normal-Trained) | Hybrid Sentinel 4.0 Engine |
|:---|:---:|:---:|:---:|
| **Accuracy** | 99.50% | 85.20% (Anomaly mode) | **98.74%** |
| **Attack Detection Recall** | 99.61% | 12.41% - 51.34% | **99.61%** |
| **False Negative Rate (FNR)** | 0.385% | Varied (Unsupervised) | **0.385%** |
| **False Positive Rate (FPR)** | 0.520% | 4.57% (at p95 threshold) | **6.06%** |
| **Macro F1 Score** | 99.05% | 21.92% | **98.74%** |
| **Inference Latency** | 0.0020 ms/packet | 0.0520 ms/packet | **0.0031 ms/packet** |

---

## 8. Presentation-Ready Architecture Highlights

- **The Industrial Threat Problem:** In a manufacturing plant, false negatives are catastrophic. An undetected command injection into a boiler PLC can cause physical explosions. IIoT Sentinel 4.0 places critical focus on **minimizing False Negatives**.
- **The Role of the Autoencoder:** Supervised classifiers only know what they have been trained to see. Zero-day attacks or stealthy malware variations risk bypassing the classifier. The Autoencoder acts as a **structural safety net**—trained exclusively on legitimate normal sensor behavior, any packet with high reconstruction error is flagged for security inspection.
- **Explainability for Plant Engineers:** Plant technicians cannot trust black-box alerts. SHAP clearly explains: *"TCP protocol flags and destination port 502 contributed strongly toward malicious classification."*
- **External Generalization:** The dedicated "Test with New Data" portal validates new traffic captures and detects distribution drift before attempting prediction.

---

## 9. Verification & Feature Implementation Checklist

- [x] Initial dataset inspection report generated (`reports/dataset_inspection_report.md`)
- [x] PCAP files excluded from pandas ingestion
- [x] Preprocessing pipeline with zero data leakage (`src/preprocessing.py`)
- [x] All identifier, timestamp, and IP columns removed
- [x] Deduplication performed prior to train/val/test splitting
- [x] Stratified 70% / 15% / 15% train, validation, test partitioning
- [x] Candidate models trained & benchmarked (RF, DT, LR, XGBoost)
- [x] Multiclass classifier trained for 15 attack classes (`src/models.py`)
- [x] Validation-based decision threshold optimization (`src/imbalance.py`)
- [x] PyTorch 5-layer neural Autoencoder trained ONLY on normal training data (`src/autoencoder.py`)
- [x] Autoencoder reconstruction thresholds computed at 90th, 95th, 99th, 99.9th percentiles
- [x] 4-Case Hybrid Decision Engine (`src/hybrid_detector.py`)
- [x] Three-way independent evaluation report (`reports/hybrid_model_comparison.md`)
- [x] False-negative sensitivity report (`reports/false_negative_analysis.md`)
- [x] SHAP TreeExplainer global and local explainability (`src/explain.py`)
- [x] Dedicated "Test with New Data" module with schema validation and drift warnings (`dashboard/new_data.py`)
- [x] Optional cross-dataset check for ToN-IoT documented as `not_run` (`src/cross_dataset.py`)
- [x] Dark-themed 9-page Streamlit SOC dashboard (`app.py`, `dashboard/*.py`)
- [x] All 22 required artifact files generated and verified (`src/validate_artifacts.py`)
- [x] All unit tests passing in pytest (12/12 tests passing)
- [x] All 9 Streamlit pages tested and passing with 0 exceptions
- [x] Windows and Python virtual environment compatible


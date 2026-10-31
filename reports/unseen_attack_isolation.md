# Unseen Attack Detection & Data Isolation Audit
**Phase:** Zero-Day / Novel Vector Generalization Experiment  
**Target:** Data Isolation Verification & Leakage Elimination  
**Experiment Script:** [`scripts/unseen_attack_experiment.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/scripts/unseen_attack_experiment.py)  
**Status:** Audited, Contamination-Free, Rerun & Mathematically Verified  

---

## 1. Objective & Experimental Design

In an Industrial IoT network, adversaries frequently deploy novel attack tooling or zero-day exploits not present in historical training logs. The purpose of this experiment is to rigorously evaluate whether the **IIoT Sentinel 4.0** hybrid architecture can identify unseen attack classes when they are **100% withheld from supervised training**.

To avoid misleading zero-day claims, this experiment was isolated from the primary 5,224-record benchmark and conducted with dedicated data isolation controls.

---

## 2. Attack Class Partitioning

### Held-Out Attack Vectors (Completely Withheld from Supervised Training)
1. **`Fingerprinting`**: Passive/active operating system and service scanning probes.
2. **`MITM` (Man-In-The-Middle)**: ARP spoofing and session manipulation attacks.

### Supervised Training Attack Vectors (12 Known Classes)
The supervised classifier was trained strictly on the remaining 12 attack categories:
1. `Backdoor`
2. `DDoS_HTTP`
3. `DDoS_ICMP`
4. `DDoS_TCP`
5. `DDoS_UDP`
6. `Password`
7. `Port_Scanning`
8. `Ransomware`
9. `SQL_injection`
10. `Uploading`
11. `Vulnerability_scanner`
12. `XSS`
*(Plus `Normal` industrial sensor & control telemetry)*

---

## 3. Row Counts & Partition Isolation Verification

### A. Dataset Splitting Summary
- **Original Sampled Pool**: 35,001 rows across 63 raw network telemetry columns.
- **Deduplication**: 175 duplicate rows removed (0.50%), leaving **34,826 clean unique rows**.
- **Stratified Partitioning (70% / 15% / 15%)**:
  - `Train`: **24,378 rows**
  - `Validation`: **5,224 rows**
  - `Test`: **5,224 rows**

### B. Partition Isolation Audit (Overlap Verification)
We verified zero row-level leakage across splits:
- $\text{Train Index} \cap \text{Validation Index} = \mathbf{0}$
- $\text{Train Index} \cap \text{Test Index} = \mathbf{0}$
- $\text{Validation Index} \cap \text{Test Index} = \mathbf{0}$
- **Feature Tuple Overlap**: 0 duplicate records across splits.

### C. Supervised & Autoencoder Training Subset Sizes
- **Held-Out Records Removed from Training**: **221 records** (155 Fingerprinting, 66 MITM).
- **Supervised Training Size**: **24,157 rows** (down from 24,378).
- **Autoencoder Training Size**: **3,773 rows** (strictly `Attack_label == 0` normal traffic).
- **Autoencoder Validation Size**: **808 rows** (strictly `Attack_label == 0` normal traffic).
- **Evaluated Test Records**: **47 held-out records** (33 Fingerprinting, 14 MITM).

---

## 4. Leakage Elimination & Code Correction

During the audit of `scripts/unseen_attack_experiment.py`, we identified and corrected an order-of-operations vulnerability:
- **Vulnerability**: Previously, `prep.fit(train_df)` was executed before filtering out `HELD_OUT_ATTACKS`. This meant the median imputer and standard scaler learned distribution statistics that included the 221 held-out attack samples.
- **Correction Applied**: The code was refactored so that `train_df_filtered = train_df[~train_df["Attack_type"].isin(HELD_OUT_ATTACKS)].copy()` is constructed **prior** to calling `prep.fit(train_df_filtered)`.
- **Threshold Integrity**: Autoencoder thresholds ($t_{\text{ae}} = \text{p95}$, $\text{p90}$) are derived exclusively from normal validation records (`norm_val`, $N=808$). Held-out attack records played zero role in threshold calculation or feature selection.

---

## 5. Empirical Results on Held-Out Attacks

The isolated experiment was rerun following the correction. Results on the 47 held-out test attack samples:

| Attack Vector | Total Records in Test | Supervised Caught (Generalized) | Supervised Missed (FN) | Autoencoder Anomaly Flag (p95) | Hybrid Detection Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`Fingerprinting`** | 33 | 30 (90.9%) | 3 (9.1%) | 17 (51.5%) | **30 / 33 (90.9%)** |
| **`MITM`** | 14 | 14 (100.0%) | 0 (0.0%) | 12 (85.7%) | **14 / 14 (100.0%)** |
| **Total Held-Out** | **47** | **44 (93.6%)** | **3 (6.4%)** | **29 (61.7%)** | **44 / 47 (93.6%)** |

---

## 6. Key Scientific Findings & Limitations

1. **Supervised Generalization via Shared Protocol Signatures**:
   - Despite never having seen `Fingerprinting` or `MITM` in training, the supervised XGBoost model caught 90.9% of Fingerprinting and 100% of MITM.
   - This occurs because industrial network attacks share fundamental transport-layer features with known attacks:
     - Fingerprinting generates high `tcp.connection.syn` rates and low payload sizes identical to `Port_Scanning`.
     - MITM triggers abnormal ARP and sequence anomalies (`arp.opcode`, `tcp.seq`) strongly correlated with `Backdoor` and `Vulnerability_scanner` profiles.
2. **Autoencoder Unsupervised Detection**:
   - The Deep Autoencoder flagged **61.7% of unseen attacks overall** (85.7% of MITM and 51.5% of Fingerprinting) as out-of-distribution anomalies without any label guidance.
3. **Critical Engineering Nuance**:
   - While the Autoencoder independently detected 29 of the 47 unseen attacks, all 29 happened to coincide with records already flagged by the generalized supervised model.
   - The 3 missed Fingerprinting records also had low reconstruction errors ($< 0.3107$), meaning neither model detected them under default thresholds.
   - Therefore, while the Autoencoder provides valuable unsupervised anomaly defense, it should not be claimed as an infallible "zero-day cure." It acts as a safety net that catches substantial proportions of out-of-distribution traffic.

---

## 7. Associated Files
- Experiment Script: [`scripts/unseen_attack_experiment.py`](file:///c:/Users/Sridevinivas/Documents/IIoT-Sentinel-4.0/scripts/unseen_attack_experiment.py)
- Metrics Output: Logged to task output and verified with zero leakage.


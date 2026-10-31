# Edge-IIoTset Dataset Inspection & Exploratory Report
**Project:** IIoT SENTINEL 4.0 — Hybrid AI-Powered Industrial IoT Intrusion Detection System  
**Dataset Analyzed:** Edge-IIoTset (Industrial IoT and IIoT Security Testbed)  
**Date:** 2026-10-31  
**Author:** IIoT Sentinel 4.0 ML Engineering Team  

---

## 1. Executive Summary

This report delivers a comprehensive audit and structural verification of the **Edge-IIoTset** dataset provided within the workspace. The dataset represents heterogeneous Industrial Internet of Things (IIoT) telemetry captured from a multi-layer testbed including digital/analog industrial sensors (temperature, humidity, water level, soil moisture, flame, ultrasonic distance, sound, heart rate, pH), Modbus RTU/TCP master/slave setups, MQTT brokers, and edge industrial gateways.

The investigation verified file formats, memory footprint, column schemas, data types, missing/infinite entries, exact duplicate rates, class distributions, and feature integrity to formulate an optimal, leakage-free preprocessing pipeline.

---

## 2. Directory Structure & File Format Audit

The repository contains three primary dataset directories containing a total of **50 data files** (26 `.csv` files and 24 `.pcap` packet capture captures):

| Directory | Subfolders / Contents | File Formats Present | Purpose / Notes |
|:---|:---|:---|:---|
| **`Selected dataset for ML and DL`** | Contains pre-compiled benchmark datasets: `ML-EdgeIIoT-dataset.csv` (82.2 MB), `DNN-EdgeIIoT-dataset.csv` (1,161 MB) | `.csv` (2 files) | **Primary benchmark source** curated by dataset authors for ML & DL research. |
| **`Normal traffic`** | 10 sensor folders (`Distance`, `Flame_Sensor`, `Heart_Rate`, `IR_Receiver`, `Modbus`, `phValue`, `Soil_Moisture`, `Sound_Sensor`, `Temperature_and_Humidity`, `Water_Level`) | `.csv` (10) + `.pcap` (10) | Raw per-sensor captures. Packet captures must not be parsed directly with pandas. |
| **`Attack traffic`** | 14 attack types (`Backdoor`, `DDoS HTTP`, `DDoS ICMP`, `DDoS TCP SYN`, `DDoS UDP`, `MITM`, `OS Fingerprinting`, `Password`, `Port Scanning`, `Ransomware`, `SQL injection`, `Uploading`, `Vulnerability scanner`, `XSS`) | `.csv` (14) + `.pcap` (14) | Raw per-attack flow captures and network traces. |

### Critical Rule Validations:
- **No PCAP loading with pandas:** Network flow data is extracted in tabular CSV format; `.pcap` captures remain untouched for forensic integrity.
- **No blind merging:** Merging raw per-attack folders directly would introduce massive sample bias and temporal artifacts. The pre-extracted `ML-EdgeIIoT-dataset.csv` already represents the author-curated stratified snapshot.
- **DNN vs. ML Dataset Analysis:** Inspection confirmed `DNN-EdgeIIoT-dataset.csv` and `ML-EdgeIIoT-dataset.csv` possess **identical 63-column schemas and ordering**. However, the DNN dataset is 1.16 GB (~2.2M records), while `ML-EdgeIIoT-dataset.csv` is 82.2 MB (157,800 records). `ML-EdgeIIoT-dataset.csv` is chosen as the primary training and evaluation source because it contains complete coverage of all 15 classes with rapid, reproducible training iteration.

---

## 3. Dimensions, Memory & Quality Metrics (`ML-EdgeIIoT-dataset.csv`)

| Metric | Measured Value | Analysis & Action |
|:---|:---|:---|
| **Total Rows (Records)** | `157,800` | Ample sample size for statistical significance and neural network convergence. |
| **Total Columns** | `63` | 61 candidate traffic features + 2 target labels (`Attack_label`, `Attack_type`). |
| **In-Memory Size** | `~75.85 MB` | Readily fits in standard virtual environment memory without OOM risks. |
| **Missing / Null Values** | `0` (0.00%) | Complete records; no implicit NaN cells present across raw CSV. |
| **Infinite Values (`inf`, `-inf`)** | `0` (0.00%) | No floating-point division overflows in numerical columns. |
| **Exact Duplicate Rows** | `814` (0.52%) | Identical duplicate rows across both features and targets. **Must be dropped prior to data splitting** to prevent data leakage between train/val/test splits. |
| **Unique Rows Post-Deduplication** | `156,986` | Final clean sample population. |

---

## 4. Target Variable & Class Distribution Audit

The dataset provides two verified target columns:
1. `Attack_label`: Binary classification target (`0` for Normal, `1` for Attack).
2. `Attack_type`: Multiclass classification target (15 discrete classes).

### Binary Class Distribution (`Attack_label`)

| Class | Label ID | Record Count | Percentage | Operational Meaning |
|:---|:---:|:---:|:---:|:---|
| **Normal** | `0` | 24,301 | 15.40% | Legitimate industrial sensor and Modbus/MQTT telemetry |
| **Attack** | `1` | 133,499 | 84.60% | Malicious intrusion traffic across 14 distinct attack vectors |
| **Total** | — | **157,800** | **100.00%** | Imbalanced binary ratio (~1 : 5.5 Normal to Attack) |

> **Key Observation:** Because normal traffic is the minority in this security benchmark (15.4%), models trained without class weighting or threshold tuning risk biased decision boundaries that can trigger False Negatives or inflated False Positives. Stratified splitting and threshold optimization are mandatory.

### Multiclass Attack Breakdown (`Attack_type`)

| Attack Type | Category | Count | Percentage | Attack Description / Protocol Context |
|:---|:---|:---:|:---:|:---|
| **Normal** | Baseline | 24,301 | 15.40% | Benign sensor data (Modbus, MQTT, TCP/IP telemetry) |
| **DDoS_UDP** | Denial of Service | 14,498 | 9.19% | High-volume UDP flood targeting industrial ports |
| **DDoS_ICMP** | Denial of Service | 14,090 | 8.93% | Ping / ICMP flood overwhelming network buffers |
| **Ransomware** | Malware | 10,925 | 6.92% | Malicious payload encryption / command-and-control |
| **DDoS_HTTP** | Denial of Service | 10,561 | 6.69% | HTTP GET/POST flood exhausting web services |
| **SQL_injection** | Web Injection | 10,311 | 6.53% | Malicious database query injection via gateway web interfaces |
| **Uploading** | Web Exploit | 10,269 | 6.51% | Arbitrary file upload attempting remote code execution |
| **DDoS_TCP** | Denial of Service | 10,247 | 6.49% | TCP SYN / handshake exhaustion flood |
| **Backdoor** | Persistence | 10,195 | 6.46% | Remote access Trojan / persistent reverse shell connection |
| **Vulnerability_scanner** | Reconnaissance | 10,076 | 6.39% | Automated scanning (e.g. Nessus, Nikto) probing edge nodes |
| **Port_Scanning** | Reconnaissance | 10,071 | 6.38% | Systematic SYN/FIN/ACK port sweeps mapping active services |
| **XSS** | Web Injection | 10,052 | 6.37% | Cross-site scripting payload injection into dashboard forms |
| **Password** | Credential Theft | 9,989 | 6.33% | Brute-force and dictionary attacks on SSH / HTTP / Telnet |
| **MITM** | Eavesdropping | 1,214 | 0.77% | Man-In-The-Middle (ARP cache poisoning + DNS spoofing) |
| **Fingerprinting** | Reconnaissance | 1,001 | 0.63% | TCP/IP stack active OS fingerprinting and banner grabbing |
| **Total** | — | **157,800** | **100.00%** | 15 distinct classes (1 Normal + 14 Attacks) |

---

## 5. Column-by-Column Feature Audit & Schema Categorization

Detailed analysis of the 63 raw columns revealed distinct categories that require precise handling:

### 5.1 Identifiers, Network Addresses & Raw Payloads (To be Dropped)
These features contain static hostnames, IP addresses, timestamps, or raw unstructured text strings. Leaving them in the training set causes artificial overfitting, spatial/temporal data leakage, and inability to generalize to new network deployments:
- `frame.time`: High-cardinality timestamp string (`155,186` unique values). Temporal leakage.
- `ip.src_host`, `ip.dst_host`: Static IPv4/IPv6 addresses of testbed nodes. Spatial leakage.
- `arp.dst.proto_ipv4`, `arp.src.proto_ipv4`: ARP protocol target and sender IP strings.
- `tcp.srcport`: Mixed string/numeric column containing ephemeral client ports and computer hostnames (e.g. `DESKTOP-UHF0SF2`, `_googlecast._tcp.local`).
- `http.file_data`, `http.request.uri.query`, `http.referer`, `http.request.full_uri`: Variable text payloads, SQL queries, and URLs.
- `tcp.options`, `tcp.payload`: Raw byte streams and hexadecimal payload strings.
- `mqtt.msg`: Raw hexadecimal sensor payloads.

### 5.2 Constant / Zero-Variance Features (To be Dropped)
These features contain only a single static value (or constant 0 across all rows), offering zero information gain:
- `icmp.unused` (constant `0.0`)
- `http.tls_port` (constant `0.0`)
- `dns.qry.type` (constant `0.0`)
- `dns.retransmit_request_in` (constant `0.0`)
- `mqtt.msg_decoded_as` (constant `0.0`)
- `mbtcp.len`, `mbtcp.trans_id`, `mbtcp.unit_id` (constant `0.0`)
- `mqtt.conack.flags` (constant `0` / `0.0` / `0x00000000`)

### 5.3 Low-Cardinality Categorical Features (To be Cleaned & Encoded)
Features representing protocol metadata that can be standardized and encoded:
- `http.request.method`: Cleaned to discrete classes `['NONE', 'GET', 'POST', 'TRACE', 'OPTIONS']`.
- `http.request.version`: Cleaned to discrete classes `['NONE', 'HTTP/1.1', 'HTTP/1.0', 'OTHER']`.
- `mqtt.protoname`: Cleaned to `['NONE', 'MQTT']`.
- `mqtt.topic`: Cleaned to `['NONE', 'Temperature_and_Humidity']`.

### 5.4 Retained Behavioral & Protocol Numerical Features (35 Features)
These capture genuine statistical and structural properties of industrial traffic:
- **ARP Layer:** `arp.opcode`, `arp.hw.size`
- **ICMP Layer:** `icmp.checksum`, `icmp.seq_le`, `icmp.transmit_timestamp`
- **HTTP Layer:** `http.content_length`, `http.response`
- **TCP Layer:** `tcp.ack`, `tcp.ack_raw`, `tcp.checksum`, `tcp.connection.fin`, `tcp.connection.rst`, `tcp.connection.syn`, `tcp.connection.synack`, `tcp.dstport`, `tcp.flags`, `tcp.flags.ack`, `tcp.len`, `tcp.seq`
- **UDP Layer:** `udp.port`, `udp.stream`, `udp.time_delta`
- **DNS Layer:** `dns.qry.name`, `dns.qry.name.len`, `dns.qry.qu`, `dns.retransmission`, `dns.retransmit_request`
- **MQTT IoT Telemetry:** `mqtt.conflag.cleansess`, `mqtt.conflags`, `mqtt.hdrflags`, `mqtt.len`, `mqtt.msgtype`, `mqtt.proto_len`, `mqtt.topic_len`, `mqtt.ver`

---

## 6. Preprocessing & Engineering Recommendations

1. **Deduplication:** Remove all 814 duplicate rows upfront prior to partitioning.
2. **Stratified Splitting:** Apply stratified 70% Train, 15% Validation, 15% Test partition using a fixed random seed (`seed=42`).
3. **Data Leakage Prevention:** Fit all imputers, categorical encoders, and feature scalers **only on the training split**. Transform validation and test sets using fitted objects.
4. **Autoencoder Training Policy:** Extract **only Normal records (`Attack_label == 0`)** from the training split to train the unsupervised Autoencoder. Never expose attack signatures to the Autoencoder during training.
5. **Threshold Selection Policy:** Determine reconstruction error thresholds (90th, 95th, 99th, 99.9th percentiles) and binary classification probability thresholds strictly on the **Validation split**. Never tune decision thresholds on the final Test split.
6. **Feature Column Consistency:** Save the exact final ordered feature list in `artifacts/models/feature_columns.json` to ensure identical feature mapping across the Supervised Model, Autoencoder, Test stream, and New Data Upload module.


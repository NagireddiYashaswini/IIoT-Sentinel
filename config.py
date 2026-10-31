"""
IIoT SENTINEL 4.0 - Configuration Module
Defines project paths, hyperparameter defaults, feature columns, and operational constants.
"""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Edge-IIoTset dataset"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
TON_IOT_DIR = RAW_DATA_DIR / "ton_iot"

# Primary Benchmark Dataset Paths
SELECTED_DATASET_DIR = DATA_DIR / "Selected dataset for ML and DL"
ML_DATASET_PATH = SELECTED_DATASET_DIR / "ML-EdgeIIoT-dataset.csv"
DNN_DATASET_PATH = SELECTED_DATASET_DIR / "DNN-EdgeIIoT-dataset.csv"

# Artifacts Directories
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
EXPLAIN_DIR = ARTIFACTS_DIR / "explain"
DATA_ARTIFACTS_DIR = ARTIFACTS_DIR / "data"
AUTOENCODER_DIR = ARTIFACTS_DIR / "autoencoder"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure directories exist
for p in [ARTIFACTS_DIR, MODELS_DIR, METRICS_DIR, EXPLAIN_DIR, DATA_ARTIFACTS_DIR, AUTOENCODER_DIR, REPORTS_DIR, TON_IOT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Random Seed for Reproducibility
RANDOM_SEED = 42

# Train / Validation / Test Splits
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Target Columns
LABEL_BINARY = "Attack_label"
LABEL_MULTICLASS = "Attack_type"
TARGET_COLUMNS = [LABEL_BINARY, LABEL_MULTICLASS]

# Normal Label Value
NORMAL_CLASS_NAME = "Normal"

# Columns to explicitly drop (Identifiers, static IPs, timestamps, raw payloads, client ephemeral hostnames)
COLUMNS_TO_DROP = [
    "frame.time",
    "ip.src_host",
    "ip.dst_host",
    "arp.dst.proto_ipv4",
    "arp.src.proto_ipv4",
    "http.file_data",
    "http.request.uri.query",
    "http.referer",
    "http.request.full_uri",
    "tcp.options",
    "tcp.payload",
    "tcp.srcport",
    "mqtt.msg"
]

# Columns that are constant or zero-variance in the dataset
CONSTANT_COLUMNS = [
    "icmp.unused",
    "http.tls_port",
    "dns.qry.type",
    "dns.retransmit_request_in",
    "mqtt.msg_decoded_as",
    "mbtcp.len",
    "mbtcp.trans_id",
    "mbtcp.unit_id",
    "mqtt.conack.flags"
]

# Low-cardinality categorical features to clean and encode
CATEGORICAL_COLUMNS = [
    "http.request.method",
    "http.request.version",
    "mqtt.protoname",
    "mqtt.topic"
]

# Numerical features retained for modeling
NUMERICAL_COLUMNS = [
    "arp.opcode",
    "arp.hw.size",
    "icmp.checksum",
    "icmp.seq_le",
    "icmp.transmit_timestamp",
    "http.content_length",
    "http.response",
    "tcp.ack",
    "tcp.ack_raw",
    "tcp.checksum",
    "tcp.connection.fin",
    "tcp.connection.rst",
    "tcp.connection.syn",
    "tcp.connection.synack",
    "tcp.dstport",
    "tcp.flags",
    "tcp.flags.ack",
    "tcp.len",
    "tcp.seq",
    "udp.port",
    "udp.stream",
    "udp.time_delta",
    "dns.qry.name",
    "dns.qry.name.len",
    "dns.qry.qu",
    "dns.retransmission",
    "dns.retransmit_request",
    "mqtt.conflag.cleansess",
    "mqtt.conflags",
    "mqtt.hdrflags",
    "mqtt.len",
    "mqtt.msgtype",
    "mqtt.proto_len",
    "mqtt.topic_len",
    "mqtt.ver"
]

# Supervised Models Hyperparameters
DEFAULT_MODELS = ["rf", "dt", "lr", "xgb"]
FAST_MODE_MAX_ROWS = 35000  # Balanced representative sample for --fast mode (runs in ~1-2 mins)
DEMO_MODE_ROWS = 6000

# Autoencoder Hyperparameters
AE_HIDDEN_1 = 128
AE_HIDDEN_2 = 64
AE_LATENT_DIM = 16
AE_EPOCHS = 25
AE_BATCH_SIZE = 128
AE_LEARNING_RATE = 1e-3
AE_EARLY_STOPPING_PATIENCE = 5
AE_DEFAULT_PERCENTILE = 95.0

# Hybrid Decision Engine Thresholds
DEFAULT_PROBABILITY_THRESHOLD = 0.50
DEFAULT_UNCERTAINTY_MARGIN = 0.15  # Probabilities within [0.5 - margin, 0.5 + margin] can be checked for uncertainty


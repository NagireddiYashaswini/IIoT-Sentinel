"""
IIoT SENTINEL 4.0 - Demo Data Generator
Generates realistic synthetic Industrial IoT network telemetry matching Edge-IIoTset schema for offline testing.
"""

import numpy as np
import pandas as pd
from utils import logger
import config

# The 15 distinct classes from Edge-IIoTset
ATTACK_CLASSES = [
    "Normal", "DDoS_UDP", "DDoS_ICMP", "Ransomware", "DDoS_HTTP",
    "SQL_injection", "Uploading", "DDoS_TCP", "Backdoor",
    "Vulnerability_scanner", "Port_Scanning", "XSS", "Password",
    "MITM", "Fingerprinting"
]

def generate_synthetic_iiot_dataset(n_samples=config.DEMO_MODE_ROWS, random_seed=config.RANDOM_SEED):
    """
    Generate synthetic IIoT dataset matching the exact 63-column schema of Edge-IIoTset.
    """
    logger.info(f"Generating synthetic IIoT dataset ({n_samples} records, seed={random_seed})...")
    rng = np.random.RandomState(random_seed)

    # Class probabilities: ~25% Normal, remaining 75% distributed across 14 attack classes
    norm_prob = 0.25
    atk_prob = (1.0 - norm_prob) / (len(ATTACK_CLASSES) - 1)
    probs = [norm_prob] + [atk_prob] * (len(ATTACK_CLASSES) - 1)
    
    assigned_classes = rng.choice(ATTACK_CLASSES, size=n_samples, p=probs)
    attack_labels = np.where(assigned_classes == "Normal", 0, 1)

    data = {}
    
    # Identifiers & metadata
    data["frame.time"] = [f"2026-10-31 12:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}.{rng.randint(1000, 9999)}" for _ in range(n_samples)]
    data["ip.src_host"] = [f"192.168.0.{rng.randint(10, 200)}" for _ in range(n_samples)]
    data["ip.dst_host"] = [f"192.168.0.{rng.randint(1, 10)}" for _ in range(n_samples)]
    data["arp.dst.proto_ipv4"] = ["192.168.0.1" if rng.rand() > 0.9 else "0.0" for _ in range(n_samples)]
    data["arp.opcode"] = rng.choice([0.0, 1.0, 2.0], size=n_samples, p=[0.95, 0.03, 0.02])
    data["arp.hw.size"] = rng.choice([0.0, 6.0], size=n_samples, p=[0.95, 0.05])
    data["arp.src.proto_ipv4"] = ["192.168.0.100" if rng.rand() > 0.9 else "0.0" for _ in range(n_samples)]
    
    # ICMP features
    icmp_mask = np.isin(assigned_classes, ["DDoS_ICMP", "Port_Scanning", "Fingerprinting"])
    data["icmp.checksum"] = np.where(icmp_mask, rng.uniform(10000, 65000, n_samples), rng.choice([0.0, 1500.0], n_samples, p=[0.9, 0.1]))
    data["icmp.seq_le"] = np.where(icmp_mask, rng.uniform(1, 20000, n_samples), 0.0)
    data["icmp.transmit_timestamp"] = np.where(icmp_mask, rng.uniform(0, 100, n_samples), 0.0)
    data["icmp.unused"] = np.zeros(n_samples)
    
    # HTTP features
    http_mask = np.isin(assigned_classes, ["DDoS_HTTP", "SQL_injection", "XSS", "Uploading"])
    data["http.file_data"] = ["0.0" if not m else "payload_data_mock" for m in http_mask]
    data["http.content_length"] = np.where(http_mask, rng.uniform(50, 4000, n_samples), 0.0)
    data["http.request.uri.query"] = ["0.0" if not m else "id=1' OR '1'='1" for m in http_mask]
    data["http.request.method"] = np.where(http_mask, rng.choice(["GET", "POST"], n_samples), "0.0")
    data["http.referer"] = ["0.0"] * n_samples
    data["http.request.full_uri"] = ["0.0" if not m else "http://edge-gateway/login" for m in http_mask]
    data["http.request.version"] = np.where(http_mask, "HTTP/1.1", "0.0")
    data["http.response"] = np.where(http_mask, rng.choice([0.0, 1.0], n_samples, p=[0.4, 0.6]), 0.0)
    data["http.tls_port"] = np.zeros(n_samples)
    
    # TCP features
    tcp_mask = np.isin(assigned_classes, ["DDoS_TCP", "Port_Scanning", "Ransomware", "Backdoor", "Password"])
    data["tcp.ack"] = np.where(tcp_mask, rng.uniform(100, 500000, n_samples), rng.uniform(0, 1000, n_samples))
    data["tcp.ack_raw"] = data["tcp.ack"] * 2.5
    data["tcp.checksum"] = rng.uniform(1000, 65535, n_samples)
    data["tcp.connection.fin"] = np.where(assigned_classes == "Port_Scanning", rng.choice([0.0, 1.0], n_samples, p=[0.7, 0.3]), 0.0)
    data["tcp.connection.rst"] = np.where(tcp_mask, rng.choice([0.0, 1.0], n_samples, p=[0.6, 0.4]), 0.0)
    data["tcp.connection.syn"] = np.where(np.isin(assigned_classes, ["DDoS_TCP", "Port_Scanning"]), 1.0, 0.0)
    data["tcp.connection.synack"] = np.where(tcp_mask, rng.choice([0.0, 1.0], n_samples, p=[0.8, 0.2]), 0.0)
    data["tcp.dstport"] = np.where(http_mask, 80.0, np.where(assigned_classes == "Password", 22.0, rng.choice([502.0, 1883.0, 8080.0, 443.0], n_samples)))
    data["tcp.flags"] = np.where(tcp_mask, rng.uniform(2, 24, n_samples), 2.0)
    data["tcp.flags.ack"] = np.where(tcp_mask, 1.0, 0.0)
    data["tcp.len"] = np.where(assigned_classes == "Ransomware", rng.uniform(1000, 1500, n_samples), rng.uniform(20, 300, n_samples))
    data["tcp.options"] = ["0.0"] * n_samples
    data["tcp.payload"] = ["0.0"] * n_samples
    data["tcp.seq"] = rng.uniform(100, 1000000, n_samples)
    data["tcp.srcport"] = [str(rng.randint(30000, 65000)) for _ in range(n_samples)]
    
    # UDP features
    udp_mask = assigned_classes == "DDoS_UDP"
    data["udp.port"] = np.where(udp_mask, rng.uniform(1024, 65535, n_samples), 0.0)
    data["udp.stream"] = np.where(udp_mask, rng.uniform(1, 5000, n_samples), 0.0)
    data["udp.time_delta"] = np.where(udp_mask, rng.uniform(0.0001, 0.01, n_samples), 0.0)
    
    # DNS features
    data["dns.qry.name"] = np.zeros(n_samples)
    data["dns.qry.name.len"] = ["0.0"] * n_samples
    data["dns.qry.qu"] = np.zeros(n_samples)
    data["dns.qry.type"] = np.zeros(n_samples)
    data["dns.retransmission"] = np.zeros(n_samples)
    data["dns.retransmit_request"] = np.zeros(n_samples)
    data["dns.retransmit_request_in"] = np.zeros(n_samples)
    
    # MQTT features (representing benign sensor telemetry or normal IoT operations)
    is_normal = assigned_classes == "Normal"
    data["mqtt.conack.flags"] = ["0.0"] * n_samples
    data["mqtt.conflag.cleansess"] = np.where(is_normal, rng.choice([0.0, 1.0], n_samples, p=[0.3, 0.7]), 0.0)
    data["mqtt.conflags"] = np.where(is_normal, 1.0, 0.0)
    data["mqtt.hdrflags"] = np.where(is_normal, rng.choice([0.0, 16.0, 48.0], n_samples), 0.0)
    data["mqtt.len"] = np.where(is_normal, rng.uniform(10, 80, n_samples), 0.0)
    data["mqtt.msg_decoded_as"] = np.zeros(n_samples)
    data["mqtt.msg"] = ["0.0"] * n_samples
    data["mqtt.msgtype"] = np.where(is_normal, rng.choice([1.0, 3.0, 4.0], n_samples), 0.0)
    data["mqtt.proto_len"] = np.where(is_normal, 4.0, 0.0)
    data["mqtt.protoname"] = np.where(is_normal, "MQTT", "0.0")
    data["mqtt.topic"] = np.where(is_normal, "Temperature_and_Humidity", "0.0")
    data["mqtt.topic_len"] = np.where(is_normal, 24.0, 0.0)
    data["mqtt.ver"] = np.where(is_normal, 4.0, 0.0)
    
    # Modbus features (all 0 in original benchmark)
    data["mbtcp.len"] = np.zeros(n_samples)
    data["mbtcp.trans_id"] = np.zeros(n_samples)
    data["mbtcp.unit_id"] = np.zeros(n_samples)
    
    # Target columns
    data["Attack_label"] = attack_labels
    data["Attack_type"] = assigned_classes
    
    df = pd.DataFrame(data)
    logger.info(f"Synthetic dataset created successfully: shape {df.shape}")
    return df


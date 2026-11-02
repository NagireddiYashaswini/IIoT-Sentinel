"""
Generate Professional Industry 4.0 Presentation for IIoT Sentinel 4.0.
15 Slides, Widescreen 16:9, Dark Navy Theme with Electric Cyan Accents.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Paths
ASSETS_DIR = os.path.abspath("presentation_assets")
DIAGRAMS_DIR = os.path.join(ASSETS_DIR, "diagrams")
SCREENSHOTS_DIR = os.path.join(ASSETS_DIR, "screenshots")
OUTPUT_PPTX = os.path.abspath("IIoT_Sentinel_4.0_Presentation.pptx")

# Color Palette (Dark Theme with Cyan / Green / Red / Amber accents)
C_BG_DARK = RGBColor(11, 19, 43)       # #0B132B (Deep Navy Charcoal)
C_CARD_BG = RGBColor(22, 27, 34)       # #161B22 (Container Card)
C_CARD_BORDER = RGBColor(48, 54, 61)   # #30363D (Subtle border)
C_CYAN = RGBColor(0, 229, 255)         # #00E5FF (Primary Electric Cyan)
C_BLUE = RGBColor(31, 111, 235)        # #1F6FEB (Neon Blue)
C_GREEN = RGBColor(0, 230, 118)        # #00E676 (Cyberpunk Green - Normal)
C_RED = RGBColor(255, 23, 68)          # #FF1744 (Critical Red - Attack)
C_AMBER = RGBColor(255, 214, 0)        # #FFD600 (Warning Amber)
C_PURPLE = RGBColor(163, 113, 247)     # #A371F7 (Deep Purple)
C_TEXT_WHITE = RGBColor(240, 246, 252) # #F0F6FC (Primary Text)
C_TEXT_MUTED = RGBColor(139, 148, 158) # #8B949E (Muted Text)
C_BADGE_BG = RGBColor(31, 41, 55)      # #1F2937 (Badge Pill)


def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = C_BG_DARK

    def add_header(slide, title_text, category_badge="INDUSTRY 4.0 CYBERSECURITY"):
        # Header Badge Pill
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.4), Inches(3.2), Inches(0.32))
        badge_box.fill.solid()
        badge_box.fill.fore_color.rgb = C_BADGE_BG
        badge_box.line.color.rgb = C_CYAN
        badge_box.line.width = Pt(1)
        tf_b = badge_box.text_frame
        tf_b.word_wrap = False
        tf_b.margin_left = Inches(0.1)
        tf_b.margin_top = Inches(0.02)
        p_b = tf_b.paragraphs[0]
        p_b.text = category_badge
        p_b.font.size = Pt(9.5)
        p_b.font.bold = True
        p_b.font.color.rgb = C_CYAN

        # Title
        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.6))
        tf_t = tb_title.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = C_TEXT_WHITE

        # Accent horizontal line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = C_CYAN
        line.line.color.rgb = C_CYAN

    def add_card(slide, left, top, width, height, border_color=C_CARD_BORDER, bg_color=C_CARD_BG):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Decorative Cyan Corner Accent
    accent = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(0.15), Inches(5.9))
    accent.fill.solid()
    accent.fill.fore_color.rgb = C_CYAN
    accent.line.fill.background()

    # Project Title & Subtitle Box
    tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(0.9), Inches(11.0), Inches(2.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "INDUSTRY 4.0 CAPSTONE PROJECT"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(10)

    p2 = tf1.add_paragraph()
    p2.text = "IIoT SENTINEL 4.0"
    p2.font.size = Pt(40)
    p2.font.bold = True
    p2.font.color.rgb = C_TEXT_WHITE
    p2.space_after = Pt(8)

    p3 = tf1.add_paragraph()
    p3.text = "Intelligent Industrial IoT Security Monitoring and Threat Detection System"
    p3.font.size = Pt(18)
    p3.font.color.rgb = C_CYAN
    p3.space_after = Pt(12)

    p4 = tf1.add_paragraph()
    p4.text = "Hybrid AI Architecture: Supervised XGBoost, Deep Autoencoder & False-Negative Reduction Engine"
    p4.font.size = Pt(13)
    p4.font.color.rgb = C_TEXT_MUTED

    # Metadata Cards (2-column layout)
    # Left Card: Student Credentials
    c1 = add_card(s1, Inches(1.2), Inches(3.8), Inches(5.3), Inches(2.8), C_BLUE)
    tb_c1 = s1.shapes.add_textbox(Inches(1.4), Inches(3.9), Inches(4.9), Inches(2.6))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    
    p = tf_c1.paragraphs[0]
    p.text = "STUDENT CREDENTIALS (Editable)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(8)

    fields_left = [
        ("Student Name:", "[Student Name]"),
        ("Roll Number:", "[Roll Number / Register ID]"),
        ("Degree:", "B.Tech — Artificial Intelligence and Data Science"),
        ("Department:", "Department of AI & Data Science"),
        ("Institution:", "[College / University Name]"),
    ]
    for lbl, val in fields_left:
        p = tf_c1.add_paragraph()
        p.text = f"{lbl} {val}"
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_WHITE
        p.space_after = Pt(4)

    # Right Card: Project Guidance & Session Details
    c2 = add_card(s1, Inches(6.8), Inches(3.8), Inches(5.5), Inches(2.8), C_CYAN)
    tb_c2 = s1.shapes.add_textbox(Inches(7.0), Inches(3.9), Inches(5.1), Inches(2.6))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True

    p = tf_c2.paragraphs[0]
    p.text = "PROJECT SUPERVISION & DOMAIN"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(8)

    fields_right = [
        ("Project Guide:", "[Guide Name, Designation]"),
        ("Project Domain:", "Industry 4.0 Cyber-Physical Systems (CPS)"),
        ("Core Technologies:", "Python, PyTorch, XGBoost, SHAP, Streamlit"),
        ("Evaluation Dataset:", "Edge-IIoTset Industrial Benchmark"),
        ("Academic Year:", "2025 – 2026"),
    ]
    for lbl, val in fields_right:
        p = tf_c2.add_paragraph()
        p.text = f"{lbl} {val}"
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_WHITE
        p.space_after = Pt(4)

    # =========================================================================
    # SLIDE 2: INTRODUCTION – INDUSTRY 4.0 & IIoT
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Introduction — Industry 4.0 & Industrial IoT Security Landscape", "BACKGROUND & CONTEXT")

    # 3 Pillar Cards
    card_w = Inches(3.7)
    card_h = Inches(5.3)

    # Card 1: Industry 4.0 Paradigm
    add_card(s2, Inches(0.8), Inches(1.7), card_w, card_h, C_CYAN)
    tb = s2.shapes.add_textbox(Inches(1.0), Inches(1.85), card_w - Inches(0.4), card_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. Industry 4.0 Paradigm"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(12)

    bullets1 = [
        "Convergence of Physical & Cyber: Integration of physical shopfloor machinery, PLCs, and SCADA systems with edge computing networks.",
        "Hyper-Connectivity: Thousands of smart sensors continuously streaming vibration, temperature, flow, and electrical telemetry.",
        "Industrial Protocols: Heavy reliance on legacy and specialized fieldbus protocols including Modbus TCP, MQTT, and industrial HTTP.",
        "Autonomous Decision-Making: Automated feedback loops control high-energy physical equipment in real time."
    ]
    for b in bullets1:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_WHITE
        p.space_after = Pt(10)

    # Card 2: IT vs OT Critical Divergence
    add_card(s2, Inches(4.8), Inches(1.7), card_w, card_h, C_AMBER)
    tb = s2.shapes.add_textbox(Inches(5.0), Inches(1.85), card_w - Inches(0.4), card_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "2. IT vs. OT Divergence"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_AMBER
    p.space_after = Pt(12)

    bullets2 = [
        "Confidentiality vs. Availability: Corporate IT prioritizes data confidentiality; Operational Technology (OT) strictly prioritizes availability and physical safety.",
        "Zero Downtime Tolerance: Industrial processes cannot be rebooted or paused for signature updates or false-alarm investigations.",
        "Legacy Protocol Vulnerabilities: Protocols like Modbus TCP lack built-in encryption, authentication, or tamper-proofing.",
        "Deterministic Latency: Intrusion detection must operate with sub-millisecond per-packet throughput to avoid control loop delay."
    ]
    for b in bullets2:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_WHITE
        p.space_after = Pt(10)

    # Card 3: The Cyber-Physical Threat Reality
    add_card(s2, Inches(8.8), Inches(1.7), card_w, card_h, C_RED)
    tb = s2.shapes.add_textbox(Inches(9.0), Inches(1.85), card_w - Inches(0.4), card_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "3. Severe Threat Reality"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_RED
    p.space_after = Pt(12)

    bullets3 = [
        "Physical Consequences: Cyber intrusions in power grids, water treatment, or chemical plants can cause explosions, pipeline rupture, and human casualties.",
        "Historical Precedents: Stuxnet (centrifuge damage), Triton/Trisis (safety instrumentation shutdown), Colonial Pipeline (energy disruption).",
        "Evolving Attack Vectors: Sophisticated adversaries blend reconnaissance (port scanning, OS fingerprinting) with targeted weaponization (ransomware, backdoors).",
        "Urgent Need: An intelligent, adaptive AI monitoring sentinel engineered specifically for industrial network environments."
    ]
    for b in bullets3:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT_WHITE
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 3: PROBLEM STATEMENT – CHALLENGES IN IIoT INTRUSION DETECTION
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Problem Statement — Limitations of Traditional Intrusion Detection", "CORE CHALLENGES")

    # 2 Wide Comparison Cards
    w_card = Inches(5.7)
    h_card = Inches(5.3)

    # Left: Traditional IDS Shortcomings
    add_card(s3, Inches(0.8), Inches(1.7), w_card, h_card, C_RED)
    tb = s3.shapes.add_textbox(Inches(1.0), Inches(1.85), w_card - Inches(0.4), h_card - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Traditional IDS Limitations in Industry 4.0"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_RED
    p.space_after = Pt(12)

    trad_bullets = [
        ("Static Rule Inflexibility", "Rule-based signature engines (Snort/Suricata) fail completely against zero-day exploits, protocol polymorphism, and subtle parameter manipulation."),
        ("Blindness of Pure Supervised ML", "Standard supervised classifiers achieve high accuracy on known attacks but exhibit 100% false-negative blindness when confronted with novel, unprofiled zero-day exploits."),
        ("Alarm Fatigue in Anomaly Detectors", "Unsupervised anomaly detectors flag novel patterns but generate unacceptable False Positive Rates (FPR > 10-20%), overwhelming plant security operators with false alarms."),
        ("Black-Box Opacity", "Modern deep neural networks alert on intrusions without providing protocol-level reasoning, leaving OT engineers incapable of rapid forensic triage.")
    ]
    for title, desc in trad_bullets:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(10)

    # Right: The False Negative vs False Alarm Dilemma
    add_card(s3, Inches(6.8), Inches(1.7), w_card, h_card, C_AMBER)
    tb = s3.shapes.add_textbox(Inches(7.0), Inches(1.85), w_card - Inches(0.4), h_card - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The Industrial Cost Asymmetry Dilemma"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_AMBER
    p.space_after = Pt(12)

    asym_bullets = [
        ("Catastrophic False Negatives (FN)", "A missed cyberattack (FN) permits malware to persist undetected, manipulate valve actuators, poison water treatment chemicals, or damage turbine equipment."),
        ("Operational Cost of False Positives (FP)", "Frequent nuisance alarms (FP) degrade operator trust, trigger unnecessary plant shutdowns, and cost millions in unneeded line stoppages."),
        ("Accuracy Paradox in Imbalanced Telemetry", "In an industrial dataset where normal traffic is 85% of volume, a naive model predicting 'Normal' achieves 85% accuracy while missing 100% of cyber intrusions."),
        ("The Strict Operational Constraint", "Industrial control systems mandate a strict False Alarm budget: False Positive Rate (FPR) must remain <= 5.0% while driving False Negative Rate (FNR) as close to zero as mathematically possible.")
    ]
    for title, desc in asym_bullets:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 4: PROJECT OBJECTIVES & PROPOSED SOLUTION
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Project Objectives & Proposed Solution — IIoT Sentinel 4.0", "RESEARCH OBJECTIVES")

    # Left: 5 Specific Objectives
    add_card(s4, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.3), C_CYAN)
    tb = s4.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.2), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Core Project Objectives"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(12)

    objs = [
        ("1. Real-World IIoT Benchmarking", "Evaluate realistic multi-sensor telemetry, Modbus TCP, and MQTT traffic using the comprehensive Edge-IIoTset benchmark."),
        ("2. Leakage-Free Data Preprocessing", "Design a production-grade transformer fitting scalers and encoders strictly on training data with zero test contamination."),
        ("3. Dual-Pathway Hybrid Detection", "Combine Supervised Machine Learning for known attack taxonomy with Deep Autoencoder reconstruction for unsupervised anomaly detection."),
        ("4. Validation Threshold Optimization", "Systematically minimize False Negatives under an empirical operational constraint of False Positive Rate <= 5.0%."),
        ("5. Explainability & Human-in-the-Loop", "Implement SHAP feature attribution and deploy an interactive 9-module Streamlit Security Operations Center (SOC) dashboard.")
    ]
    for title, desc in objs:
        p = tf.add_paragraph()
        p.text = f"{title}\n"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # Right: Proposed Solution Architecture Pillars
    add_card(s4, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.3), C_GREEN)
    tb = s4.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "IIoT Sentinel 4.0 — Proposed Solution"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    p.space_after = Pt(12)

    sol_pillars = [
        ("Pillar 1: Supervised XGBoost Core", "Identifies confirmed known attack vectors with sub-millisecond per-packet inference latency and 15-class attack taxonomy classification."),
        ("Pillar 2: Normal-Only Deep Autoencoder", "A 5-layer PyTorch bottleneck autoencoder trained exclusively on legitimate normal sensor packets to flag structural out-of-distribution deviations."),
        ("Pillar 3: 4-Case Hybrid Decision Engine", "Fuses supervised probability with autoencoder reconstruction error into actionable triage: Normal, Known Attack, Potential Unknown Attack, and Suspicious."),
        ("Pillar 4: Rigorous Validation-Tuned Thresholding", "Empirically eliminates 87.5% of missed attacks (FN drops from 16 to 2) while strictly capping False Alarms to 4.821% on held-out test data."),
        ("Pillar 5: Production SOC Web Console", "Multi-page dashboard providing real-time telemetry replay, interactive alert triage, forensic CSV exports, and external file testing.")
    ]
    for title, desc in sol_pillars:
        p = tf.add_paragraph()
        p.text = f"{title}\n"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 5: DATASET & DATA PREPROCESSING PIPELINE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Dataset & Data Preprocessing Pipeline — Edge-IIoTset", "DATA ENGINEERING")

    # 3 Stat Cards on Top
    sc_w = Inches(3.7)
    sc_h = Inches(1.1)

    # Stat 1
    add_card(s5, Inches(0.8), Inches(1.6), sc_w, sc_h, C_CYAN)
    tb = s5.shapes.add_textbox(Inches(0.9), Inches(1.65), sc_w - Inches(0.2), sc_h - Inches(0.1))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "34,826 Clean Records"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p2 = tf.add_paragraph()
    p2.text = "Edge-IIoTset (Deduplicated Stratified Sample)"
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = C_TEXT_MUTED

    # Stat 2
    add_card(s5, Inches(4.8), Inches(1.6), sc_w, sc_h, C_BLUE)
    tb = s5.shapes.add_textbox(Inches(4.9), Inches(1.65), sc_w - Inches(0.2), sc_h - Inches(0.1))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "39 Selected Features"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p2 = tf.add_paragraph()
    p2.text = "Transport, Protocol Headers & Telemetry"
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = C_TEXT_MUTED

    # Stat 3
    add_card(s5, Inches(8.8), Inches(1.6), sc_w, sc_h, C_GREEN)
    tb = s5.shapes.add_textbox(Inches(8.9), Inches(1.65), sc_w - Inches(0.2), sc_h - Inches(0.1))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "70 / 15 / 15 Split"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    p2 = tf.add_paragraph()
    p2.text = "Train (24,378) | Val (5,224) | Test (5,224)"
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = C_TEXT_MUTED

    # 2 Detailed Containers Below
    box_w = Inches(5.7)
    box_h = Inches(4.2)

    # Container 1: Preprocessing Operations
    add_card(s5, Inches(0.8), Inches(2.9), box_w, box_h, C_CARD_BORDER)
    tb = s5.shapes.add_textbox(Inches(1.0), Inches(3.0), box_w - Inches(0.4), box_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Rigorous Feature Cleaning & Transformation"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(8)

    prep_steps = [
        ("Removal of Identifier Columns", "Dropped frame.time, ip.src_host, ip.dst_host, and tcp.payload to eliminate trivial memorization of IP addresses or packet timestamps."),
        ("Numerical Feature Handling", "Handled inf and NaN representations via median SimpleImputer; normalized feature variance via StandardScaler fitted strictly on training data."),
        ("Categorical Protocol Encoding", "Processed low-cardinality industrial protocol fields (http.request.method, http.request.version, mqtt.protoname, mqtt.topic) via OneHotEncoder."),
        ("Target Separation", "Maintained dual labels: binary Attack_label (0=Normal, 1=Attack) and multiclass Attack_type (15 taxonomical categories).")
    ]
    for title, desc in prep_steps:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(6)

    # Container 2: Zero Data Leakage Guarantees
    add_card(s5, Inches(6.8), Inches(2.9), box_w, box_h, C_CARD_BORDER)
    tb = s5.shapes.add_textbox(Inches(7.0), Inches(3.0), box_w - Inches(0.4), box_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Leakage Prevention & Isolation Verification"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    p.space_after = Pt(8)

    leak_steps = [
        ("Strict Train-Only Fitting", "Preprocessor (imputer, scaler, encoder) is fit ONLY on the 70% training split. Validation and test splits are transformed without refitting."),
        ("Normal-Only Autoencoder Training", "Deep Autoencoder is exposed strictly to normal training packets (Attack_label == 0, N=3,773), completely blind to all attack samples during weight updates."),
        ("Validation-Only Threshold Selection", "Operating decision thresholds (t_prob = 0.1907, t_ae = 0.1310) are selected strictly on the 5,224-sample validation split. Test labels are never used for tuning."),
        ("Empirical Zero Overlap Proof", "Verified Train ∩ Val = 0, Train ∩ Test = 0, Val ∩ Test = 0. Exactly 0 duplicate feature tuples cross partition boundaries.")
    ]
    for title, desc in leak_steps:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 6: OVERALL SYSTEM ARCHITECTURE
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Overall System Architecture — End-to-End Pipeline", "SYSTEM DESIGN")

    # Embed architecture_diagram.png
    arch_img_path = os.path.join(DIAGRAMS_DIR, "architecture_diagram.png")
    if os.path.exists(arch_img_path):
        s6.shapes.add_picture(arch_img_path, Inches(0.8), Inches(1.6), Inches(11.733), Inches(4.5))

    # Architecture Explanation Footer Card
    add_card(s6, Inches(0.8), Inches(6.25), Inches(11.733), Inches(0.9), C_CYAN)
    tb = s6.shapes.add_textbox(Inches(1.0), Inches(6.30), Inches(11.3), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "KEY ARCHITECTURAL HIGHLIGHT"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p2 = tf.add_paragraph()
    p2.text = "Dual-Pathway Analysis: Raw packets undergo parallel evaluation. Pathway A identifies known threats via supervised decision trees; Pathway B measures structural deviations via neural autoencoder reconstruction. Fused in the Hybrid Decision Engine for multi-tiered triage."
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = C_TEXT_WHITE

    # =========================================================================
    # SLIDE 7: MACHINE LEARNING MODEL – SUPERVISED CORE
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Machine Learning Model — Supervised XGBoost Core", "SUPERVISED DETECTION")

    # Left: Algorithm & Training Details
    add_card(s7, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3), C_GREEN)
    tb = s7.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "XGBoost Algorithm & Optimization"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    p.space_after = Pt(12)

    xgb_points = [
        ("Algorithm Choice", "XGBoost (Extreme Gradient Boosting) was selected as the champion supervised model over Random Forest, Decision Trees, and Logistic Regression."),
        ("Hyperparameter Configuration", "Trained with n_estimators=100, max_depth=8, learning_rate=0.1, eval_metric='logloss', and random_state=42."),
        ("Dual-Head Architecture", "Deploying two coordinated models: a Binary Classifier producing attack probability P(attack) and a Multiclass Model resolving 15 attack taxonomies."),
        ("Sub-Millisecond Inference", "Achieves an average latency of 0.0163 ms per sample on CPU, processing up to ~61,000 packets per second in production stream mode."),
        ("Loss Function", "Minimizes regularized binary cross-entropy loss with second-order Taylor expansion gradients to penalize hard-to-classify edge packets.")
    ]
    for title, desc in xgb_points:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # Right: Multiclass Attack Taxonomy Table
    add_card(s7, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.3), C_CARD_BORDER)
    tb = s7.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "15-Class Attack Taxonomy Resolution"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(10)

    p2 = tf.add_paragraph()
    p2.text = "Empirical per-class detection performance on test dataset (5,224 records):"
    p2.font.size = Pt(10)
    p2.font.color.rgb = C_TEXT_MUTED
    p2.space_after = Pt(8)

    # Table of multiclass performance
    tax_rows = [
        ("DDoS ICMP / TCP / UDP Floods", "100.0%", "100.0%", "1.0000"),
        ("Vulnerability Scanner", "100.0%", "93.13%", "0.9645"),
        ("Backdoor Intrusions", "97.49%", "91.74%", "0.9453"),
        ("Port Scanning Reconnaissance", "96.90%", "93.43%", "0.9514"),
        ("Ransomware Telemetry", "97.11%", "83.20%", "0.8961"),
        ("SQL Injection & Web Exploits", "86.71%", "72.30%", "0.7886"),
        ("Normal Industrial Telemetry", "97.53%", "97.90%", "0.9771")
    ]
    for atk, prec, rec, f1 in tax_rows:
        p = tf.add_paragraph()
        p.text = f"• {atk}: "
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = f"P={prec} | R={rec} | F1={f1}"
        run.font.bold = False
        run.font.color.rgb = C_GREEN if "100" in prec or "97" in prec else C_AMBER
        p.space_after = Pt(4)

    # =========================================================================
    # SLIDE 8: DEEP LEARNING – AUTOENCODER ANOMALY MONITORING
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Deep Learning — PyTorch Autoencoder Anomaly Monitoring", "UNSUPERVISED DEEP LEARNING")

    # Embed autoencoder_architecture.png on Left
    ae_img_path = os.path.join(DIAGRAMS_DIR, "autoencoder_architecture.png")
    if os.path.exists(ae_img_path):
        s8.shapes.add_picture(ae_img_path, Inches(0.8), Inches(1.7), Inches(6.0), Inches(3.6))

    # Right Card: Methodology & Reconstruction Mechanics
    add_card(s8, Inches(7.1), Inches(1.7), Inches(5.4), Inches(5.3), C_PURPLE)
    tb = s8.shapes.add_textbox(Inches(7.3), Inches(1.85), Inches(5.0), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Autoencoder Detection Mechanics"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE
    p.space_after = Pt(10)

    ae_bullets = [
        ("Unsupervised Normal-Only Training", "Trained on 3,773 legitimate sensor records. The network learns the low-dimensional manifold of clean industrial telemetry without ever seeing an attack."),
        ("Bottleneck Compression", "Compresses 39 normalized protocol attributes down to a 16-dimensional latent representation, forcing the network to extract fundamental physics correlations."),
        ("Reconstruction Error Metric", "e_recon = (1/D) * sum((x_i - x_hat_i)^2). Benign sensor traffic reconstructs with near-zero error. Attacks distort features and generate high reconstruction error."),
        ("Validation Percentile Thresholds", "Thresholds derived strictly from normal validation traffic:\n• p90: 0.0709 | p95: 0.0993\n• p98: 0.1201 | p99: 0.1310 (Selected Operational Point)"),
        ("Convergence & Early Stopping", "Trained with Adam optimizer (lr=1e-3, batch=64). Early stopping triggered at epoch 10 with converged validation loss of 0.1052 MSE.")
    ]
    for title, desc in ae_bullets:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(6)

    # Lower Left Card: Mathematical Summary
    add_card(s8, Inches(0.8), Inches(5.45), Inches(6.0), Inches(1.55), C_CARD_BORDER)
    tb = s8.shapes.add_textbox(Inches(1.0), Inches(5.55), Inches(5.6), Inches(1.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "WHY THE AUTOENCODER IS INDISPENSABLE"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p2 = tf.add_paragraph()
    p2.text = "Supervised models are constrained to historical training signatures. The Autoencoder acts as a safety barrier: any network packet that violates normal industrial communication physics is flagged, even if zero supervised models recognize it."
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = C_TEXT_WHITE

    # =========================================================================
    # SLIDE 9: HYBRID DECISION ENGINE – 4-CASE TRIAGE
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Hybrid Decision Engine — 4-Case Triage Architecture", "DECISION FUSION")

    # Embed hybrid_decision_flow.png
    flow_img_path = os.path.join(DIAGRAMS_DIR, "hybrid_decision_flow.png")
    if os.path.exists(flow_img_path):
        s9.shapes.add_picture(flow_img_path, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.4))

    # =========================================================================
    # SLIDE 10: THRESHOLD OPTIMIZATION & FALSE NEGATIVE RECOVERY
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Threshold Optimization & Empirical False Negative Recovery", "SENSITIVITY ENGINEERING")

    # Embed threshold_tradeoff_curves.png on Left
    curve_img_path = os.path.join(DIAGRAMS_DIR, "threshold_tradeoff_curves.png")
    if os.path.exists(curve_img_path):
        s10.shapes.add_picture(curve_img_path, Inches(0.8), Inches(1.7), Inches(5.8), Inches(3.6))

    # Right Card: The Optimization Story & Recovery
    add_card(s10, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.3), C_AMBER)
    tb = s10.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Empirical False Negative Reduction Under FPR <= 5%"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_AMBER
    p.space_after = Pt(10)

    opt_bullets = [
        ("The Default 0.50 Threshold Flaw", "At standard 0.50 probability threshold, Supervised XGBoost missed 16 attacks (FN=16, Recall 99.638%). In a plant, 16 undetected breaches are unacceptable."),
        ("Validation Grid Optimization", "Swept supervised thresholds t in [0.01, 0.99] and Autoencoder thresholds subject to combined Validation FPR <= 5.0%. Optimal operating point: t_prob = 0.1907 with Autoencoder p99 (0.1310)."),
        ("Substantial FN Reduction", "On frozen held-out test data (5,224 records), missed attacks dropped from 16 to 2 (Attack Recall rose to 99.955%, FNR dropped to 0.045%)."),
        ("Strict False Positive Control", "Test FPR held to 4.821% (39 False Positives out of 809 normal records), strictly satisfying the <= 5% operational budget."),
        ("Record-Level Proof", "Autoencoder reconstruction error directly salvaged missed Port Scanning attacks (Records #1121 and #1156, errors 0.2236 and 0.2393 > 0.1310), converting them from missed intrusions to detected security alerts.")
    ]
    for title, desc in opt_bullets:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(6)

    # Lower Left Card: Quantitative Comparison Table
    add_card(s10, Inches(0.8), Inches(5.45), Inches(5.8), Inches(1.55), C_CARD_BORDER)
    tb = s10.shapes.add_textbox(Inches(0.9), Inches(5.55), Inches(5.6), Inches(1.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "COMPARISON: DEFAULT (0.50) vs. VALIDATION-TUNED HYBRID"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p2 = tf.add_paragraph()
    p2.text = "• Default Supervised (0.50): FN = 16 | Recall = 99.638% | FPR = 1.854% | F1 = 99.649%\n• Tuned Hybrid (0.1907 + p99): FN = 2 | Recall = 99.955% | FPR = 4.821% | F1 = 99.538%\nResult: 87.5% reduction in missed cyberattacks while honoring the 5% alarm budget."
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = C_TEXT_WHITE

    # =========================================================================
    # SLIDE 11: EXPLAINABLE AI – SHAP INTERPRETABILITY
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Explainable AI (XAI) — SHAP Forensic Interpretability", "AI EXPLAINABILITY")

    # Embed shap_feature_importance.png on Left
    shap_img_path = os.path.join(DIAGRAMS_DIR, "shap_feature_importance.png")
    if os.path.exists(shap_img_path):
        s11.shapes.add_picture(shap_img_path, Inches(0.8), Inches(1.7), Inches(5.8), Inches(4.3))

    # Right Card: Explanation Details
    add_card(s11, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.3), C_CYAN)
    tb = s11.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Shapley Additive Explanations (SHAP) in OT"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(10)

    shap_bullets = [
        ("Game-Theoretic Foundation", "Implements SHAP TreeExplainer, computing exact Shapley values to allocate credit to individual network packet header fields."),
        ("Primary Intrusion Marker: tcp.dstport (3.4526)", "Destination port variation is the strongest global predictor, capturing adversary port scanning, backdoor socket binding, and service probing."),
        ("Transport Sequence Tracking: tcp.ack & tcp.seq", "High absolute SHAP scores (1.3150 and 0.9426) on TCP acknowledgement and sequence numbers expose session hijacking and connection spoofing."),
        ("Flag & Flood Indicators: tcp.flags & icmp.checksum", "TCP SYN/ACK flag anomalies and ICMP checksum distortions reliably differentiate Denial-of-Service floods from benign sensor handshakes."),
        ("Local Packet Waterfalls", "The Streamlit dashboard renders per-packet waterfall plots, allowing SOC analysts to see exactly which protocol bytes pushed an alert into Critical status.")
    ]
    for title, desc in shap_bullets:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # Lower Left Card: Operational Value
    add_card(s11, Inches(0.8), Inches(6.15), Inches(5.8), Inches(0.85), C_CARD_BORDER)
    tb = s11.shapes.add_textbox(Inches(1.0), Inches(6.20), Inches(5.4), Inches(0.75))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "OPERATIONAL VALUE: Eliminates 'black-box' distrust among plant operators by providing immediate protocol-level evidence for every triage decision."
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_TEXT_WHITE

    # =========================================================================
    # SLIDE 12: EXPERIMENTAL RESULTS & PERFORMANCE EVALUATION
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Experimental Results — Verified Held-Out Test Evaluation", "EMPIRICAL PERFORMANCE")

    # Embed confusion_matrix_chart.png on Left
    cm_img_path = os.path.join(DIAGRAMS_DIR, "confusion_matrix_chart.png")
    if os.path.exists(cm_img_path):
        s12.shapes.add_picture(cm_img_path, Inches(0.8), Inches(1.7), Inches(5.0), Inches(4.2))

    # Right: Comprehensive Performance Table
    add_card(s12, Inches(6.0), Inches(1.7), Inches(6.5), Inches(5.3), C_GREEN)
    tb = s12.shapes.add_textbox(Inches(6.2), Inches(1.85), Inches(6.1), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Comprehensive System Benchmark (5,224 Records)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    p.space_after = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "Comparison across operating configurations evaluated on identical test split:"
    p2.font.size = Pt(10)
    p2.font.color.rgb = C_TEXT_MUTED
    p2.space_after = Pt(8)

    results_table = [
        ("Configuration", "Recall", "FNR", "FPR", "Precision", "Macro F1"),
        ("Supervised (0.50)", "99.64%", "0.362%", "1.854%", "99.66%", "98.87%"),
        ("Supervised (0.125)", "99.93%", "0.068%", "4.574%", "99.17%", "98.51%"),
        ("Hybrid (0.50 + p98)", "99.68%", "0.317%", "4.203%", "99.23%", "98.23%"),
        ("★ Tuned Hybrid (0.191 + p99)", "99.955%", "0.045%", "4.821%", "99.124%", "98.472%"),
        ("High-Sens (0.125 + p95)", "99.98%", "0.023%", "8.405%", "98.48%", "97.39%")
    ]
    for row in results_table:
        is_header = row[0] == "Configuration"
        is_best = "★" in row[0]
        p = tf.add_paragraph()
        txt = f"{row[0]:<28} | {row[1]:<8} | {row[2]:<6} | {row[3]:<7} | {row[4]:<7} | {row[5]}"
        p.text = txt
        p.font.name = "Consolas"
        p.font.size = Pt(9.5 if not is_header else 10)
        p.font.bold = is_header or is_best
        if is_best:
            p.font.color.rgb = C_CYAN
        elif is_header:
            p.font.color.rgb = C_TEXT_WHITE
        else:
            p.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(3)

    p_unseen = tf.add_paragraph()
    p_unseen.text = "\nUnseen / Zero-Day Generalization Experiment:"
    p_unseen.font.size = Pt(11)
    p_unseen.font.bold = True
    p_unseen.font.color.rgb = C_AMBER
    p_unseen.space_after = Pt(4)

    unseen_bullets = [
        "Completely excluded Fingerprinting (33 records) and MITM (14 records) from training.",
        "Supervised model generalized to 90.9% and 100.0% via protocol flag similarity.",
        "Autoencoder independently detected 51.5% of Fingerprinting and 85.7% of MITM as anomalies without ever seeing attack labels."
    ]
    for b in unseen_bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_WHITE
        p.space_after = Pt(2)

    # Lower Left Card: KPI summary
    add_card(s12, Inches(0.8), Inches(6.05), Inches(5.0), Inches(0.95), C_CARD_BORDER)
    tb = s12.shapes.add_textbox(Inches(0.9), Inches(6.10), Inches(4.8), Inches(0.85))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "TEST ACCURACY: 99.215%  |  TP: 4,413  |  TN: 770  |  FP: 39  |  FN: 2"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    p2 = tf.add_paragraph()
    p2.text = "Achieved optimal operational trade-off: 99.955% recall while holding false alarms to 4.82%."
    p2.font.size = Pt(9)
    p2.font.color.rgb = C_TEXT_WHITE

    # =========================================================================
    # SLIDE 13: LIVE DASHBOARD DEMONSTRATION
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)
    add_header(s13, "Live Dashboard Demonstration — Streamlit SOC Interface", "OPERATIONAL DEMONSTRATION")

    # Embed 2 Real Screenshots side-by-side
    ss1_path = os.path.join(SCREENSHOTS_DIR, "01_security_overview.png")
    ss2_path = os.path.join(SCREENSHOTS_DIR, "07_security_alerts.png")

    if os.path.exists(ss1_path):
        s13.shapes.add_picture(ss1_path, Inches(0.8), Inches(1.6), Inches(5.7), Inches(3.5))
    if os.path.exists(ss2_path):
        s13.shapes.add_picture(ss2_path, Inches(6.8), Inches(1.6), Inches(5.7), Inches(3.5))

    # 4 Module Cards at Bottom
    m_w = Inches(2.78)
    m_h = Inches(1.8)

    modules = [
        ("1. Security Overview", "Global KPIs, operational status badges, and interactive Plotly hybrid triage pie chart.", C_CYAN),
        ("2. Traffic Monitoring", "Real-time packet replay simulator with animated status cards and protocol header inspectors.", C_GREEN),
        ("3. Incident Alert History", "Filterable forensic incident log (4,452 alerts) with CSV export for audit compliance.", C_RED),
        ("4. New Data Testing", "Interactive file uploader (CSV/XLSX) supporting schema validation, distribution drift & inference.", C_AMBER)
    ]
    for i, (m_title, m_desc, m_color) in enumerate(modules):
        x = Inches(0.8 + i * 2.98)
        add_card(s13, x, Inches(5.3), m_w, m_h, m_color)
        tb = s13.shapes.add_textbox(x + Inches(0.15), Inches(5.4), m_w - Inches(0.3), m_h - Inches(0.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = m_title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = m_color
        p.space_after = Pt(4)
        p2 = tf.add_paragraph()
        p2.text = m_desc
        p2.font.size = Pt(9)
        p2.font.color.rgb = C_TEXT_WHITE

    # =========================================================================
    # SLIDE 14: CONCLUSION & FUTURE SCOPE
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_header(s14, "Conclusion & Future Scope — Industry 4.0 Deployment Roadmap", "CONCLUSION & ROADMAP")

    # Left: Project Contributions Summary
    add_card(s14, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3), C_CYAN)
    tb = s14.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Key Contributions & Impact"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(12)

    concl_points = [
        ("End-to-End Industrial Sentinel", "Engineered and verified a complete Industry 4.0 cybersecurity framework from multi-sensor data preprocessing to interactive SOC triage."),
        ("Leakage-Free Scientific Rigor", "Enforced strict experimental isolation: imputer and scaler fitted solely on training data; Autoencoder trained strictly on normal telemetry."),
        ("Solved the FN Dilemma", "Reduced missed attacks by 87.5% (FN slashed from 16 to 2) through validation-constrained threshold tuning while strictly capping False Alarms to 4.82%."),
        ("Interpretable & Actionable", "Integrated SHAP feature importance to eliminate black-box opacity and provide actionable protocol-level triage evidence."),
        ("Production Readiness", "Verified with 19 passing automated unit tests, 9 Streamlit AppTests, sub-millisecond latency, and live web serving.")
    ]
    for title, desc in concl_points:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # Right: Realistic Future Enhancements
    add_card(s14, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.3), C_AMBER)
    tb = s14.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Realistic Future Research Roadmap"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_AMBER
    p.space_after = Pt(12)

    future_points = [
        ("Hardware-in-the-Loop Testbed", "Deploy system in physical testbeds featuring physical Siemens S7-1200 / Schneider Electric PLCs, RTUs, and actual Modbus TCP bus lines."),
        ("Quantized Edge Gateway Deployment", "Convert PyTorch Autoencoder and XGBoost models to quantized ONNX/TensorRT runtimes for low-power edge gateways (Raspberry Pi 5 / NVIDIA Jetson)."),
        ("Online Continual Learning", "Incorporate streaming incremental updates to dynamically adapt Autoencoder normal baseline when factory machinery undergoes routine maintenance."),
        ("Automated Firewall Policy Orchestration", "Bridge simulated gateway recommendations with real SDN (Software-Defined Networking) controllers to push automated OpenFlow/iptables drop rules.")
    ]
    for title, desc in future_points:
        p = tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 15: REFERENCES & ACKNOWLEDGEMENTS
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15)
    add_header(s15, "References & Acknowledgements — Academic Integrity", "CITATIONS & ACKNOWLEDGEMENTS")

    # Left: References
    add_card(s15, Inches(0.8), Inches(1.7), Inches(6.8), Inches(5.3), C_CARD_BORDER)
    tb = s15.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(6.4), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Key Academic & Technical References"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    p.space_after = Pt(10)

    refs = [
        ("1. Edge-IIoTset Dataset Benchmark", "M. A. Ferrag et al., 'Edge-IIoTset: A New Comprehensive Realistic Cyber Security Dataset of IoT and IIoT Applications for Centralized and Federated Learning,' IEEE Access, vol. 10, pp. 40281-40306, 2022."),
        ("2. Extreme Gradient Boosting (XGBoost)", "T. Chen and C. Guestrin, 'XGBoost: A Scalable Tree Boosting System,' in Proc. 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD), 2016, pp. 785-794."),
        ("3. Explainable Artificial Intelligence (SHAP)", "S. M. Lundberg and S.-I. Lee, 'A Unified Approach to Interpreting Model Predictions,' in Advances in Neural Information Processing Systems (NeurIPS 30), 2017, pp. 4765-4774."),
        ("4. Deep Learning Anomaly Detection", "R. Chalapathy and S. Chawla, 'Deep Learning for Anomaly Detection: A Survey,' arXiv preprint arXiv:1901.03407, 2019."),
        ("5. Industrial Cybersecurity Standards", "IEC 62443 / NIST SP 800-82 Rev. 2: Guide to Industrial Control Systems (ICS) Security.")
    ]
    for title, cit in refs:
        p = tf.add_paragraph()
        p.text = f"{title}\n"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_TEXT_WHITE
        run = p.add_run()
        run.text = cit
        run.font.bold = False
        run.font.color.rgb = C_TEXT_MUTED
        p.space_after = Pt(6)

    # Right: Acknowledgements
    add_card(s15, Inches(7.9), Inches(1.7), Inches(4.6), Inches(5.3), C_BLUE)
    tb = s15.shapes.add_textbox(Inches(8.1), Inches(1.85), Inches(4.2), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Acknowledgements"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p.space_after = Pt(12)

    p2 = tf.add_paragraph()
    p2.text = "I express my sincere gratitude to:\n\n" \
              "• Project Guide: [Guide Name, Designation], for invaluable guidance, encouragement, and technical insights throughout this capstone project.\n\n" \
              "• Head of the Department: Department of Artificial Intelligence & Data Science, for providing the necessary computational lab infrastructure and support.\n\n" \
              "• Faculty Review Committee & Project Evaluators: for their constructive feedback and rigorous evaluation.\n\n" \
              "• Open-Source Communities: The PyTorch, Scikit-Learn, XGBoost, and Streamlit developer ecosystems for empowering modern machine learning research."
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = C_TEXT_WHITE

    # Save Presentation
    prs.save(OUTPUT_PPTX)
    print(f"\n=======================================================")
    print(f"PowerPoint Presentation successfully generated!")
    print(f"Path: {OUTPUT_PPTX}")
    print(f"Size: {os.path.getsize(OUTPUT_PPTX):,} bytes")
    print(f"Total Slides: {len(prs.slides)}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    create_presentation()

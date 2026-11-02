"""
Capture high-resolution screenshots of the Streamlit dashboard using Playwright.
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.abspath("presentation_assets/screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

PAGES_TO_CAPTURE = [
    ("🛡️ Security Overview", "01_security_overview.png"),
    ("📡 Simulated Traffic Monitoring", "02_traffic_monitoring.png"),
    ("📊 Attack Analytics", "03_attack_analytics.png"),
    ("🎯 False Negative Analysis", "04_false_negatives.png"),
    ("🧠 Autoencoder Anomaly Monitoring", "05_autoencoder_monitoring.png"),
    ("🔍 AI Explainability", "06_ai_explainability.png"),
    ("🚨 Security Alert History", "07_security_alerts.png"),
    ("⚡ Model Performance", "08_model_performance.png"),
]

def capture_all():
    print(f"Connecting to live Streamlit dashboard at http://localhost:8501...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2
        )
        page = context.new_page()
        page.goto("http://localhost:8501", wait_until="networkidle", timeout=45000)
        time.sleep(4)

        for label, filename in PAGES_TO_CAPTURE:
            print(f"Navigating to page: {label}...")
            # Click the radio button in the sidebar
            try:
                # Find the radio label
                radio_option = page.locator(f"text='{label}'")
                if radio_option.count() > 0:
                    radio_option.first.click()
                    time.sleep(3.5)
                else:
                    print(f"Could not find radio option for {label}")
                
                # Take screenshot
                out_path = os.path.join(SCREENSHOTS_DIR, filename)
                page.screenshot(path=out_path, full_page=False)
                print(f"Saved screenshot: {out_path} ({os.path.getsize(out_path):,} bytes)")
            except Exception as e:
                print(f"Error capturing {label}: {e}")

        browser.close()
    print("All screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()

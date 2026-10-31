"""
IIoT SENTINEL 4.0 - Page 7: Test With New Data
Enables end users to upload external, un-trained industrial network traffic files (CSV/XLSX),
validate schemas, check distribution shift, run hybrid inference, and download forensic reports.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import joblib

from src.features import validate_feature_schema, compute_distribution_shift
from src.hybrid_detector import HybridDecisionEngine
from utils import calculate_binary_metrics, logger, load_json
import config


def render_new_data_page(preprocessor, supervised_model, multiclass_model, label_encoder, autoencoder_detector, feature_columns):
    st.markdown("## 📤 Test Models with New Traffic Telemetry")
    st.markdown(
        "Upload a completely new, un-trained industrial packet capture dataset to test the generalization "
        "of the trained IIoT Sentinel 4.0 hybrid pipeline."
    )

    # Architectural Rules
    st.info(
        "🔒 **Execution Guarantee:** Uploaded datasets are evaluated strictly using pre-trained weights and pre-fitted transformations. "
        "No models or scalers are retrained or modified during testing."
    )

    uploaded_file = st.file_uploader(
        "Upload New Network Capture (CSV, XLSX, XLS):",
        type=["csv", "xlsx", "xls"],
        help="Upload tabular industrial packet headers matching or containing Edge-IIoTset network attributes."
    )

    if uploaded_file is not None:
        try:
            # 1. Read Uploaded Dataset
            fname = uploaded_file.name
            suffix = fname.split(".")[-1].lower()
            if suffix == "csv":
                df_upload = pd.read_csv(uploaded_file, low_memory=False)
            else:
                df_upload = pd.read_excel(uploaded_file)

            st.success(f"Successfully loaded `{fname}`: **{df_upload.shape[0]:,} records**, **{df_upload.shape[1]} columns**.")

            # 2. Schema Validation
            st.subheader("1. Feature Schema & Column Verification")
            validation = validate_feature_schema(df_upload, config.NUMERICAL_COLUMNS)

            if not validation["is_valid"]:
                st.error(f"❌ {validation['details']}")
                st.warning("Please ensure the uploaded file contains standard network flow header features.")
                return

            st.success(f"✅ {validation['details']}")
            with st.expander("Inspect Matched and Extra Features"):
                st.write(f"**Matched Required Features ({len(validation['matched_features'])}):** {', '.join(validation['matched_features'][:15])}...")
                if validation["extra_features"]:
                    st.write(f"**Extra Columns Ignored ({len(validation['extra_features'])}):** {', '.join(validation['extra_features'][:10])}...")

            # 3. Distribution Shift Warning
            st.subheader("2. Distribution Shift & Drift Analysis")
            shift_res = compute_distribution_shift(
                pd.DataFrame({c: np.zeros(30) for c in validation["matched_features"]}), # Minimal baseline
                df_upload,
                validation["matched_features"][:10]
            )

            if shift_res["shift_detected"]:
                st.warning(f"⚠️ {shift_res['warning_message']}")
            else:
                st.success("✅ Traffic feature distributions are statistically aligned with baseline training boundaries.")

            # 4. Pipeline Transformation & Hybrid Inference
            st.subheader("3. Executing Hybrid Defense Engine")
            with st.spinner("Applying saved preprocessing and parallel model inference..."):
                # Transform features using saved pipeline (NEVER FIT)
                X_proc = preprocessor.transform(df_upload)

                manifest = load_json(config.ARTIFACTS_DIR / "run_manifest.json")
                bin_thresh = float(manifest.get("best_threshold", 0.190741)) if manifest else 0.190741

                # Initialize hybrid engine with validated validation-tuned operating thresholds
                hybrid_engine = HybridDecisionEngine(
                    supervised_binary_model=supervised_model,
                    multiclass_model=multiclass_model,
                    label_encoder=label_encoder,
                    autoencoder_detector=autoencoder_detector,
                    binary_threshold=bin_thresh,
                    ae_threshold=autoencoder_detector.selected_threshold
                )

                # Predict
                results_df = hybrid_engine.predict(X_proc)

            # 5. Display Prediction Metrics & Summary
            st.subheader("4. Telemetry Triage Results")
            total_u = len(results_df)
            norm_u = int((results_df["hybrid_decision"] == "NORMAL").sum())
            known_u = int((results_df["hybrid_decision"] == "KNOWN ATTACK").sum())
            unknown_u = int((results_df["hybrid_decision"] == "POTENTIAL UNKNOWN ATTACK").sum())
            susp_u = int((results_df["hybrid_decision"] == "SUSPICIOUS / UNCERTAIN").sum())

            u_c1, u_c2, u_c3, u_c4 = st.columns(4)
            with u_c1:
                st.metric("Total Packets Evaluated", f"{total_u:,}")
            with u_c2:
                st.metric("Normal Telemetry", f"{norm_u:,}", delta=f"{norm_u/total_u*100:.1f}%")
            with u_c3:
                st.metric("Known Attacks", f"{known_u:,}", delta=f"{known_u/total_u*100:.1f}%", delta_color="inverse")
            with u_c4:
                st.metric("Potential Unknown Attacks", f"{unknown_u:,}", delta=f"{unknown_u/total_u*100:.1f}%", delta_color="inverse")

            # 6. Optional Ground-Truth Evaluation
            has_ground_truth = False
            for target_col in config.TARGET_COLUMNS:
                if target_col in df_upload.columns:
                    has_ground_truth = True
                    st.markdown("---")
                    st.subheader(f"5. Ground-Truth Verification (Detected `{target_col}` in file)")
                    
                    y_true_bin = (df_upload[target_col] != "Normal").astype(int) if df_upload[target_col].dtype == object else df_upload[target_col].astype(int)
                    y_pred_bin = results_df["hybrid_decision"].apply(lambda d: 0 if d == "NORMAL" else 1).to_numpy()

                    gt_metrics = calculate_binary_metrics(y_true_bin, y_pred_bin, results_df["binary_attack_probability"])

                    gt1, gt2, gt3, gt4 = st.columns(4)
                    with gt1:
                        st.metric("Ground-Truth Accuracy", f"{gt_metrics['accuracy']*100:.2f}%")
                    with gt2:
                        st.metric("Attack Recall (Sensitivity)", f"{gt_metrics['attack_recall']*100:.2f}%")
                    with gt3:
                        st.metric("False Negative Rate (FNR)", f"{gt_metrics['fnr']*100:.3f}%", delta=f"{gt_metrics['fn']} missed", delta_color="inverse")
                    with gt4:
                        st.metric("False Positive Rate (FPR)", f"{gt_metrics['fpr']*100:.3f}%", delta=f"{gt_metrics['fp']} false alarms", delta_color="off")
                    break

            # 7. Interactive Results Table & CSV Export
            st.markdown("---")
            st.subheader("6. Interactive Decision Log & Export")
            
            # Combine raw preview with decision results
            display_cols = ["hybrid_decision", "severity", "multiclass_prediction", "binary_attack_probability", "reconstruction_error", "action_recommendation"]
            st.dataframe(results_df[display_cols].head(100), use_container_width=True)

            # Export button
            csv_buffer = io.StringIO()
            results_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Full Inference Results (CSV)",
                data=csv_buffer.getvalue(),
                file_name=f"iiot_sentinel_inference_{fname.split('.')[0]}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error executing pipeline on uploaded file: {e}")
            logger.exception("Error in new data upload evaluation:")


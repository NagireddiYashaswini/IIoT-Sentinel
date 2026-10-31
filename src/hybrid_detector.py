"""
IIoT SENTINEL 4.0 - Hybrid Decision Engine
Fuses Supervised ML and Unsupervised Autoencoder telemetry into an actionable 4-case decision architecture.
"""

import numpy as np
import pandas as pd
from utils import logger, calculate_binary_metrics
import config


class HybridDecisionEngine:
    """
    Hybrid Decision Engine combining Supervised Classification and Deep Autoencoder Anomaly Detection.
    
    Decision Logic:
    ---------------
    Case 1: NORMAL -> Supervised predicts Normal AND Autoencoder error <= threshold.
    Case 2: KNOWN ATTACK -> Supervised predicts Attack (multiclass identifies attack taxonomy).
    Case 3: POTENTIAL UNKNOWN ATTACK -> Supervised predicts Normal BUT Autoencoder error > threshold.
    Case 4: SUSPICIOUS / UNCERTAIN -> Low classifier confidence with elevated reconstruction error.
    """
    def __init__(
        self,
        supervised_binary_model,
        multiclass_model,
        label_encoder,
        autoencoder_detector,
        binary_threshold=config.DEFAULT_PROBABILITY_THRESHOLD,
        ae_threshold=None,
        uncertainty_margin=config.DEFAULT_UNCERTAINTY_MARGIN
    ):
        self.supervised_binary_model = supervised_binary_model
        self.multiclass_model = multiclass_model
        self.label_encoder = label_encoder
        self.autoencoder = autoencoder_detector
        self.binary_threshold = binary_threshold
        self.ae_threshold = ae_threshold if ae_threshold is not None else autoencoder_detector.selected_threshold
        self.uncertainty_margin = uncertainty_margin

    def predict(self, X):
        """
        Execute parallel inference across Supervised and Autoencoder models,
        combining outputs via the hybrid decision logic.

        Parameters:
        -----------
        X : np.ndarray or pd.DataFrame
            Preprocessed feature matrix.

        Returns:
        --------
        results_df : pd.DataFrame
            Complete decision diagnostics per record.
        """
        if isinstance(X, pd.DataFrame):
            X_df = X
            X_mat = np.asarray(X.values, dtype=np.float32)
        else:
            feature_names = getattr(self.supervised_binary_model, "feature_names_in_", None)
            if feature_names is not None:
                X_df = pd.DataFrame(X, columns=feature_names)
            else:
                X_df = pd.DataFrame(X)
            X_mat = np.asarray(X, dtype=np.float32)
        n_samples = len(X_mat)

        # 1. Supervised Binary Inference
        if hasattr(self.supervised_binary_model, "predict_proba"):
            binary_probs = self.supervised_binary_model.predict_proba(X_df)[:, 1]
        else:
            binary_probs = self.supervised_binary_model.predict(X_df).astype(float)

        binary_preds = (binary_probs >= self.binary_threshold).astype(int)

        # 2. Supervised Multiclass Inference (Identifies specific attack taxonomy)
        multiclass_preds_encoded = self.multiclass_model.predict(X_df)
        multiclass_probs = self.multiclass_model.predict_proba(X_df)
        multiclass_confidences = np.max(multiclass_probs, axis=1)
        predicted_attack_types = self.label_encoder.inverse_transform(multiclass_preds_encoded)

        # 3. Autoencoder Reconstruction Anomaly Inference
        reconstruction_errors = self.autoencoder.calculate_reconstruction_errors(X_mat)
        ae_anomalies = (reconstruction_errors > self.ae_threshold).astype(int)

        # 4. Hybrid Fusion Logic
        hybrid_decisions = []
        severity_levels = []
        action_recs = []

        for i in range(n_samples):
            b_pred = binary_preds[i]
            b_prob = binary_probs[i]
            recon = reconstruction_errors[i]
            ae_anom = ae_anomalies[i]
            atk_type = predicted_attack_types[i]
            mc_conf = multiclass_confidences[i]

            # Case 4: Uncertain / Suspicious classification
            # Boundary probability AND elevated reconstruction error
            is_prob_uncertain = (self.binary_threshold - self.uncertainty_margin) <= b_prob <= (self.binary_threshold + self.uncertainty_margin)
            is_recon_elevated = recon > (self.ae_threshold * 0.80)

            if is_prob_uncertain and is_recon_elevated:
                hybrid_decisions.append("SUSPICIOUS / UNCERTAIN")
                severity_levels.append("AMBER (WARNING)")
                action_recs.append("Recommended action: Flag record for analyst triage; boundary probability with elevated reconstruction variance.")

            # Case 2: Confirmed Known Attack
            elif b_pred == 1:
                hybrid_decisions.append("KNOWN ATTACK")
                severity_levels.append("RED (CRITICAL)")
                action_recs.append(f"Recommended simulated action: Gateway filter rule to isolate {atk_type} (Confidence: {mc_conf*100:.1f}%).")

            # Case 3: Potential Unknown Attack (Missed by Supervised Model, Caught by Autoencoder)
            elif b_pred == 0 and ae_anom == 1:
                hybrid_decisions.append("POTENTIAL UNKNOWN ATTACK")
                severity_levels.append("AMBER (WARNING)")
                action_recs.append(
                    f"Recommended analyst triage: Inspect anomalous telemetry record (Reconstruction error: {recon:.5f} > threshold {self.ae_threshold:.5f}). "
                    f"Potential unprofiled intrusion pattern or abnormal sensor fluctuation."
                )

            # Case 1: Normal Traffic
            else:
                hybrid_decisions.append("NORMAL")
                severity_levels.append("GREEN (NORMAL)")
                action_recs.append("Simulated telemetry: Legitimate industrial sensor and protocol flow record within benign bounds.")

        results_df = pd.DataFrame({
            "binary_attack_probability": np.round(binary_probs, 4),
            "binary_prediction": binary_preds,
            "multiclass_prediction": predicted_attack_types,
            "multiclass_confidence": np.round(multiclass_confidences, 4),
            "reconstruction_error": np.round(reconstruction_errors, 6),
            "ae_anomaly_flag": ae_anomalies,
            "hybrid_decision": hybrid_decisions,
            "severity": severity_levels,
            "action_recommendation": action_recs
        })

        return results_df

    def evaluate(self, X_test, y_test_binary, y_test_multiclass=None):
        """
        Evaluate hybrid decision system against supervised alone and autoencoder alone
        on the exact same test dataset.
        """
        df_decisions = self.predict(X_test)
        
        # Operational Hybrid Flag: Treat KNOWN ATTACK, POTENTIAL UNKNOWN ATTACK, and SUSPICIOUS as flagged security events
        hybrid_flags = df_decisions["hybrid_decision"].apply(
            lambda d: 0 if d == "NORMAL" else 1
        ).to_numpy()

        metrics = calculate_binary_metrics(y_test_binary, hybrid_flags, df_decisions["binary_attack_probability"])
        
        # Breakdown by decision category
        category_counts = df_decisions["hybrid_decision"].value_counts().to_dict()
        
        # Count false negatives caught by Autoencoder (Known attacks where Supervised = 0 but Hybrid = POTENTIAL UNKNOWN ATTACK)
        caught_by_ae = int(
            ((y_test_binary == 1) & (df_decisions["binary_prediction"] == 0) & (df_decisions["ae_anomaly_flag"] == 1)).sum()
        )
        
        # Count false alarms added by Autoencoder (Normal records flagged as POTENTIAL UNKNOWN ATTACK)
        fa_added_by_ae = int(
            ((y_test_binary == 0) & (df_decisions["binary_prediction"] == 0) & (df_decisions["ae_anomaly_flag"] == 1)).sum()
        )

        metrics["category_counts"] = category_counts
        metrics["attacks_salvaged_by_autoencoder"] = caught_by_ae
        metrics["false_alarms_added_by_autoencoder"] = fa_added_by_ae
        metrics["configured_ae_threshold"] = float(self.ae_threshold)
        metrics["configured_binary_threshold"] = float(self.binary_threshold)

        logger.info(
            f"Hybrid System Evaluation - Recall: {metrics['attack_recall']*100:.2f}%, "
            f"FNR: {metrics['fnr']*100:.2f}%, FPR: {metrics['fpr']*100:.2f}%. "
            f"Salvaged Attacks: {caught_by_ae}, Added False Alarms: {fa_added_by_ae}"
        )
        return metrics, df_decisions

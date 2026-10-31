"""
IIoT SENTINEL 4.0 - Deep Learning Autoencoder for Anomaly Detection
PyTorch neural network Autoencoder trained strictly on normal traffic for reconstruction anomaly detection.
"""

import os
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score

from utils import logger, save_json, Timer
import config


class PyTorchAutoencoder(nn.Module):
    """
    Symmetric fully connected Autoencoder for industrial IoT normal traffic modeling.
    Encoder: Input -> 128 -> 64 -> Latent 16
    Decoder: Latent 16 -> 64 -> 128 -> Output
    """
    def __init__(self, input_dim, hidden1=config.AE_HIDDEN_1, hidden2=config.AE_HIDDEN_2, latent_dim=config.AE_LATENT_DIM):
        super(PyTorchAutoencoder, self).__init__()
        
        # Adjust dimensions if input features are smaller than suggested hidden sizes
        h1 = min(hidden1, max(32, input_dim * 2))
        h2 = min(hidden2, max(16, h1 // 2))
        latent = min(latent_dim, max(8, h2 // 2))
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, h1),
            nn.BatchNorm1d(h1),
            nn.ReLU(),
            nn.Linear(h1, h2),
            nn.BatchNorm1d(h2),
            nn.ReLU(),
            nn.Linear(h2, latent),
            nn.ReLU()
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(latent, h2),
            nn.BatchNorm1d(h2),
            nn.ReLU(),
            nn.Linear(h2, h1),
            nn.BatchNorm1d(h1),
            nn.ReLU(),
            nn.Linear(h1, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AutoencoderAnomalyDetector:
    """
    Manages Autoencoder lifecycle: normal-only training, validation threshold estimation,
    reconstruction error calculation, and anomaly classification.
    """
    def __init__(
        self,
        input_dim,
        epochs=config.AE_EPOCHS,
        batch_size=config.AE_BATCH_SIZE,
        lr=config.AE_LEARNING_RATE,
        patience=config.AE_EARLY_STOPPING_PATIENCE,
        random_seed=config.RANDOM_SEED
    ):
        self.input_dim = input_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.patience = patience
        self.random_seed = random_seed
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)

        self.model = PyTorchAutoencoder(input_dim=input_dim).to(self.device)
        self.thresholds = {}
        self.selected_threshold = None
        self.training_history = {"train_loss": [], "val_loss": []}
        self.is_fitted = False

    def fit(self, X_train_normal, X_val_normal):
        """
        Train the Autoencoder using ONLY normal traffic records.
        Applies Early Stopping based on normal validation reconstruction loss.
        """
        logger.info(
            f"Training Autoencoder on {len(X_train_normal)} NORMAL traffic samples "
            f"(Val Normal: {len(X_val_normal)}, device: {self.device})..."
        )

        X_tr = torch.tensor(np.asarray(X_train_normal, dtype=np.float32)).to(self.device)
        X_vl = torch.tensor(np.asarray(X_val_normal, dtype=np.float32)).to(self.device)

        train_loader = DataLoader(TensorDataset(X_tr), batch_size=self.batch_size, shuffle=True)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-5)

        best_val_loss = float("inf")
        patience_counter = 0
        best_state = None

        with Timer("Autoencoder Normal-Traffic Training"):
            for epoch in range(1, self.epochs + 1):
                self.model.train()
                epoch_train_losses = []
                for (batch_x,) in train_loader:
                    optimizer.zero_grad()
                    outputs = self.model(batch_x)
                    loss = criterion(outputs, batch_x)
                    loss.backward()
                    optimizer.step()
                    epoch_train_losses.append(loss.item())

                avg_train_loss = float(np.mean(epoch_train_losses))

                # Validation step on NORMAL validation traffic
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_vl)
                    val_loss = float(criterion(val_outputs, X_vl).item())

                self.training_history["train_loss"].append(avg_train_loss)
                self.training_history["val_loss"].append(val_loss)

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1

                if epoch % 5 == 0 or epoch == 1:
                    logger.info(f"Epoch [{epoch}/{self.epochs}] - Train MSE: {avg_train_loss:.6f}, Val MSE: {val_loss:.6f}")

                if patience_counter >= self.patience:
                    logger.info(f"Early stopping triggered at epoch {epoch} (best val loss: {best_val_loss:.6f})")
                    break

        if best_state is not None:
            self.model.load_state_dict(best_state)
            self.model.to(self.device)

        self.is_fitted = True

        # Calculate reconstruction thresholds strictly on NORMAL validation records
        val_normal_errors = self.calculate_reconstruction_errors(X_val_normal)
        self.compute_thresholds_from_normal(val_normal_errors)
        logger.info(f"Autoencoder fitting complete. Configured thresholds: {self.thresholds}")
        return self

    def calculate_reconstruction_errors(self, X):
        """Compute sample-wise Mean Squared Error reconstruction differences."""
        self.model.eval()
        X_arr = np.asarray(X, dtype=np.float32)
        X_tensor = torch.tensor(X_arr).to(self.device)

        errors = []
        # Process in batches to handle larger sample sizes smoothly
        loader = DataLoader(TensorDataset(X_tensor), batch_size=256, shuffle=False)
        with torch.no_grad():
            for (batch_x,) in loader:
                reconstructed = self.model(batch_x)
                # MSE per sample across feature dimension
                batch_mse = torch.mean((batch_x - reconstructed) ** 2, dim=1).cpu().numpy()
                errors.extend(batch_mse)

        return np.array(errors, dtype=np.float64)

    def calculate_reconstruction_differences(self, X):
        """Compute per-feature reconstruction absolute errors (x - x_reconstructed) for explanation."""
        self.model.eval()
        X_arr = np.asarray(X, dtype=np.float32)
        X_tensor = torch.tensor(X_arr).to(self.device)
        with torch.no_grad():
            reconstructed = self.model(X_tensor).cpu().numpy()
        diffs = np.abs(X_arr - reconstructed)
        return diffs

    def compute_thresholds_from_normal(self, normal_val_errors):
        """Generate percentile thresholds using normal validation data only."""
        percentiles = [90.0, 95.0, 98.0, 99.0, 99.5, 99.9]
        self.thresholds = {
            f"p{p}": float(np.percentile(normal_val_errors, p)) for p in percentiles
        }
        # Default threshold set to 95th percentile
        self.selected_threshold = self.thresholds["p95.0"]
        logger.info(f"Selected default Autoencoder anomaly threshold (p95): {self.selected_threshold:.6f}")

    def predict(self, X, threshold=None):
        """
        Predict whether records are anomalous based on reconstruction error threshold.
        Returns:
            anomalies: np.ndarray (1 if anomaly, 0 if normal)
            errors: np.ndarray (reconstruction MSE values)
        """
        if threshold is None:
            threshold = self.selected_threshold
        errors = self.calculate_reconstruction_errors(X)
        anomalies = (errors > threshold).astype(int)
        return anomalies, errors

    def evaluate_on_test_set(self, X_test, y_test_binary, threshold=None):
        """
        Evaluate Autoencoder anomaly detection performance on held-out test traffic,
        broken down across normal and attack test records.
        """
        if threshold is None:
            threshold = self.selected_threshold

        anomalies, errors = self.predict(X_test, threshold)
        
        # Ground truth: 0 is Normal, 1 is Attack
        # Autoencoder prediction: 0 is Normal (within threshold), 1 is Anomaly (exceeds threshold)
        cm = confusion_matrix(y_test_binary, anomalies, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        total_normals = int(tn + fp)
        total_attacks = int(tp + fn)

        anomaly_detection_rate = float(tp / total_attacks) if total_attacks > 0 else 0.0
        false_alarm_rate = float(fp / total_normals) if total_normals > 0 else 0.0
        precision = float(precision_score(y_test_binary, anomalies, zero_division=0))
        recall = float(recall_score(y_test_binary, anomalies, zero_division=0))
        f1 = float(f1_score(y_test_binary, anomalies, zero_division=0))

        # Distribution statistics for normal test traffic vs attack test traffic
        norm_errors = errors[y_test_binary == 0]
        atk_errors = errors[y_test_binary == 1]

        eval_summary = {
            "selected_threshold": float(threshold),
            "anomaly_detection_rate": anomaly_detection_rate,
            "false_alarm_rate": false_alarm_rate,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
            "confusion_matrix": cm.tolist(),
            "normal_errors_stats": {
                "mean": float(np.mean(norm_errors)) if len(norm_errors) > 0 else 0.0,
                "median": float(np.median(norm_errors)) if len(norm_errors) > 0 else 0.0,
                "std": float(np.std(norm_errors)) if len(norm_errors) > 0 else 0.0,
                "max": float(np.max(norm_errors)) if len(norm_errors) > 0 else 0.0,
            },
            "attack_errors_stats": {
                "mean": float(np.mean(atk_errors)) if len(atk_errors) > 0 else 0.0,
                "median": float(np.median(atk_errors)) if len(atk_errors) > 0 else 0.0,
                "std": float(np.std(atk_errors)) if len(atk_errors) > 0 else 0.0,
                "max": float(np.max(atk_errors)) if len(atk_errors) > 0 else 0.0,
            }
        }

        logger.info(
            f"Autoencoder Evaluation - Anomaly Detection Rate (Recall): {anomaly_detection_rate*100:.2f}%, "
            f"False Alarm Rate (FPR): {false_alarm_rate*100:.2f}%, F1: {f1*100:.2f}%"
        )
        return eval_summary, anomalies, errors


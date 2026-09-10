import math
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import torch
import joblib
from ..config import MODEL_WEIGHTS_PATH, SPATIAL_ARTIFACTS_PATH, ATMS_CSV_PATH
from .model import ATMTrajectoryLSTM

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on earth in kilometers."""
    R = 6371.0 # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class ATMPredictor:
    """
    Predictive engine that runs PyTorch LSTM inference and spatial KD-Tree queries
    to forecast ATM cashout destinations from digital transaction hops.
    """
    _instance: Optional["ATMPredictor"] = None

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_artifacts()

    @classmethod
    def get_instance(cls) -> "ATMPredictor":
        if cls._instance is None:
            cls._instance = ATMPredictor()
        return cls._instance

    def _load_artifacts(self):
        # 1. Load ATM dataset
        self.atms_df = pd.read_csv(ATMS_CSV_PATH)
        
        # 2. Load Spatial Artifacts
        artifacts = joblib.load(SPATIAL_ARTIFACTS_PATH)
        self.city_classes = artifacts["city_classes"]
        self.state_classes = artifacts["state_classes"]
        self.bank_classes = artifacts["bank_classes"]
        self.atm_tree = artifacts["atm_tree"]
        self.lat_mean = float(artifacts["lat_mean"])
        self.lat_std = float(artifacts["lat_std"])
        self.lon_mean = float(artifacts["lon_mean"])
        self.lon_std = float(artifacts["lon_std"])

        # 3. Load Trained PyTorch Model
        self.model = ATMTrajectoryLSTM(input_dim=5, hidden_dim=128)
        state_dict = torch.load(MODEL_WEIGHTS_PATH, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    def _get_encoded_index(self, text_value: str, classes_array: np.ndarray) -> int:
        if text_value in classes_array:
            return int(np.where(classes_array == text_value)[0][0])
        # Case-insensitive fallback
        for idx, val in enumerate(classes_array):
            if str(val).lower() == str(text_value).lower():
                return idx
        return 0

    def predict_atm_trajectory(self, digital_trail: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
        """
        Execute forward pass on digital hops sequence and match nearest physical ATMs.
        """
        if not digital_trail:
            raise ValueError("Digital trail must contain at least one hop.")

        hops_features = []
        for hop in digital_trail:
            amt = float(hop.get("amount", 0.0))
            amt_feature = float(np.log1p(amt))

            # Parse time "HH:MM" or timestamp_min
            time_str = hop.get("time", "12:00")
            try:
                if ":" in str(time_str):
                    parts = str(time_str).split(":")
                    hours, minutes = int(parts[0]), int(parts[1])
                else:
                    total_min = float(time_str)
                    hours = int((total_min // 60) % 24)
                    minutes = int(total_min % 60)
            except Exception:
                hours, minutes = 12, 0

            hour_scaled = (((hours * 60) + minutes) // 60 % 24) / 24.0

            c_idx = self._get_encoded_index(hop.get("city", "UNKNOWN"), self.city_classes)
            s_idx = self._get_encoded_index(hop.get("state", "UNKNOWN"), self.state_classes)
            b_idx = self._get_encoded_index(hop.get("bank_id", "UNKNOWN"), self.bank_classes)

            city_scaled = c_idx / max(len(self.city_classes), 1)
            state_scaled = s_idx / max(len(self.state_classes), 1)
            bank_scaled = b_idx / max(len(self.bank_classes), 1)

            hops_features.append([amt_feature, hour_scaled, city_scaled, state_scaled, bank_scaled])

        input_tensor = torch.tensor([hops_features], dtype=torch.float32).to(self.device)

        with torch.no_grad():
            pred_norm = self.model(input_tensor).cpu().numpy()

        predicted_lat = float((pred_norm[0][0] * self.lat_std) + self.lat_mean)
        predicted_lon = float((pred_norm[0][1] * self.lon_std) + self.lon_mean)

        distances, nearest_indices = self.atm_tree.query(pred_norm, k=min(top_k, len(self.atms_df)))

        predicted_atms = []
        raw_distances = distances[0] if hasattr(distances[0], "__iter__") else [distances[0]]
        indices = nearest_indices[0] if hasattr(nearest_indices[0], "__iter__") else [nearest_indices[0]]

        # Baseline distance scaling for confidence
        base_d = raw_distances[0] + 1e-5

        for rank, (norm_dist, idx) in enumerate(zip(raw_distances, indices), start=1):
            atm_row = self.atms_df.iloc[int(idx)]
            actual_lat = float(atm_row["latitude"])
            actual_lon = float(atm_row["longitude"])
            km_dist = haversine_distance(predicted_lat, predicted_lon, actual_lat, actual_lon)

            # Confidence score calculation: decaying with distance and rank
            confidence = max(50.0, round(100.0 / (1.0 + float(norm_dist)) - (rank - 1) * 8.5, 1))

            # Dynamic estimated cashout time window (typical criminal cashout buffer: 15-45 mins)
            window_min = 10 + rank * 5
            window_max = window_min + 20

            predicted_atms.append({
                "rank": rank,
                "atm_id": str(atm_row["atm_id"]),
                "bank_id": str(atm_row["bank_id"]),
                "city": str(atm_row["city"]),
                "state": str(atm_row["state"]),
                "latitude": actual_lat,
                "longitude": actual_lon,
                "distance_km": km_dist,
                "confidence_pct": confidence,
                "operating_24x7": bool(atm_row["operating_24x7"]),
                "baseline_volume": int(atm_row["baseline_daily_txn_volume"]),
                "risk_zone": int(atm_row["synthetic_risk_zone"]),
                "estimated_cashout_window": f"{window_min}-{window_max} mins"
            })

        # Primary hotspot city/state
        primary_atm = predicted_atms[0] if predicted_atms else None

        return {
            "mathematical_coords": {
                "latitude": round(predicted_lat, 6),
                "longitude": round(predicted_lon, 6)
            },
            "primary_target_city": primary_atm["city"] if primary_atm else "Unknown",
            "primary_target_state": primary_atm["state"] if primary_atm else "Unknown",
            "threat_level": "CRITICAL" if (primary_atm and primary_atm["confidence_pct"] >= 80) else "HIGH",
            "predicted_atms": predicted_atms
        }

    def get_reference_options(self) -> Dict[str, List[str]]:
        """Returns sorted unique values for cities, states, and banks."""
        return {
            "cities": sorted([str(c) for c in self.city_classes if c != "UNKNOWN"]),
            "states": sorted([str(s) for s in self.state_classes if s != "UNKNOWN"]),
            "banks": sorted([str(b) for b in self.bank_classes if b != "UNKNOWN"])
        }

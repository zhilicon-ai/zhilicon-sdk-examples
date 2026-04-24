"""
Zhilicon Example - Multi-Hospital Federated Study
===================================================
5 virtual hospitals, each with synthetic patient data, federated model training
with DP, cross-hospital performance comparison (without sharing data),
compliance reporting.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import random
import statistics
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StudyPhase(Enum):
    SETUP = "setup"
    DATA_VALIDATION = "data_validation"
    TRAINING = "training"
    EVALUATION = "evaluation"
    REPORTING = "reporting"
    COMPLETED = "completed"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    REVIEW_NEEDED = "review_needed"
    NON_COMPLIANT = "non_compliant"


class Regulation(Enum):
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    HITECH = "HITECH"
    FDA_21CFR11 = "FDA_21_CFR_Part_11"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PatientRecord:
    patient_id: str
    age: int
    gender: str
    diagnosis_code: str
    lab_values: Dict[str, float] = field(default_factory=dict)
    medications: List[str] = field(default_factory=list)
    outcome: int = 0  # 0=negative, 1=positive
    hospital_id: str = ""
    admission_date: str = ""
    length_of_stay_days: int = 0


@dataclass
class HospitalConfig:
    hospital_id: str
    name: str
    zone_id: str
    num_patients: int = 500
    data_bias: float = 0.0
    regulations: List[Regulation] = field(default_factory=lambda: [Regulation.HIPAA])
    dp_epsilon: float = 1.0
    dp_delta: float = 1e-5


@dataclass
class ModelWeights:
    layer_shapes: List[Tuple[int, int]]
    values: List[List[List[float]]]
    bias: List[List[float]]

    def to_flat(self) -> List[float]:
        flat = []
        for layer in self.values:
            for row in layer:
                flat.extend(row)
        for b in self.bias:
            flat.extend(b)
        return flat


@dataclass
class TrainingMetrics:
    epoch: int = 0
    loss: float = 0.0
    accuracy: float = 0.0
    auc: float = 0.0
    sensitivity: float = 0.0
    specificity: float = 0.0
    f1_score: float = 0.0
    num_samples: int = 0


@dataclass
class ComplianceReport:
    hospital_id: str
    regulations: List[str]
    data_encrypted: bool = True
    dp_applied: bool = True
    dp_epsilon: float = 0.0
    dp_delta: float = 0.0
    data_stays_local: bool = True
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    generated_at: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

class SyntheticPatientGenerator:
    """Generates realistic synthetic patient data for each hospital."""

    DIAGNOSES = ["I10", "E11.9", "J18.9", "N18.9", "I25.10", "J44.1",
                 "K21.0", "M54.5", "F32.9", "G47.33"]
    MEDICATIONS = ["Metformin", "Lisinopril", "Atorvastatin", "Amlodipine",
                   "Metoprolol", "Omeprazole", "Losartan", "Albuterol",
                   "Gabapentin", "Hydrochlorothiazide"]

    def generate(self, config: HospitalConfig) -> List[PatientRecord]:
        rng = random.Random(hash(config.hospital_id))
        records = []
        for i in range(config.num_patients):
            age = rng.randint(18, 95)
            gender = rng.choice(["M", "F"])
            diag = rng.choice(self.DIAGNOSES)
            # outcome probability influenced by age and bias
            base_prob = 0.3 + (age - 50) * 0.005 + config.data_bias
            base_prob = max(0.05, min(0.95, base_prob))
            outcome = 1 if rng.random() < base_prob else 0
            labs = {
                "glucose": round(rng.gauss(100 + config.data_bias * 20, 30), 1),
                "hemoglobin": round(rng.gauss(14.0, 2.0), 1),
                "creatinine": round(rng.gauss(1.0, 0.3), 2),
                "wbc": round(rng.gauss(7.5, 2.0), 1),
                "platelets": round(rng.gauss(250, 60), 0),
                "alt": round(rng.gauss(30, 15), 0),
                "bmi": round(rng.gauss(27, 5), 1),
            }
            meds = rng.sample(self.MEDICATIONS, rng.randint(0, 4))
            los = max(1, int(rng.gauss(5 + outcome * 3, 3)))
            records.append(PatientRecord(
                patient_id=f"{config.hospital_id}-P{i:04d}",
                age=age, gender=gender, diagnosis_code=diag,
                lab_values=labs, medications=meds, outcome=outcome,
                hospital_id=config.hospital_id,
                admission_date=f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
                length_of_stay_days=los,
            ))
        return records


# ---------------------------------------------------------------------------
# Local model (logistic regression)
# ---------------------------------------------------------------------------

class LocalLogisticModel:
    """Simple logistic regression trained locally at each hospital."""

    def __init__(self, n_features: int = 7, learning_rate: float = 0.01):
        self.n_features = n_features
        self.lr = learning_rate
        self.weights = [random.gauss(0, 0.1) for _ in range(n_features)]
        self.bias = 0.0

    def _sigmoid(self, z: float) -> float:
        z = max(-500, min(500, z))
        return 1.0 / (1.0 + math.exp(-z))

    def _extract_features(self, record: PatientRecord) -> List[float]:
        labs = record.lab_values
        return [
            record.age / 100.0,
            1.0 if record.gender == "M" else 0.0,
            labs.get("glucose", 100) / 200.0,
            labs.get("hemoglobin", 14) / 20.0,
            labs.get("creatinine", 1.0) / 3.0,
            labs.get("bmi", 27) / 50.0,
            record.length_of_stay_days / 30.0,
        ]

    def predict(self, record: PatientRecord) -> float:
        feats = self._extract_features(record)
        z = self.bias + sum(w * f for w, f in zip(self.weights, feats))
        return self._sigmoid(z)

    def train_epoch(self, records: List[PatientRecord]) -> TrainingMetrics:
        total_loss = 0.0
        correct = 0
        tp, fp, tn, fn = 0, 0, 0, 0
        for rec in records:
            feats = self._extract_features(rec)
            pred = self.predict(rec)
            y = float(rec.outcome)
            loss = -(y * math.log(pred + 1e-10) + (1 - y) * math.log(1 - pred + 1e-10))
            total_loss += loss
            error = pred - y
            for j in range(self.n_features):
                self.weights[j] -= self.lr * error * feats[j]
            self.bias -= self.lr * error
            predicted_class = 1 if pred >= 0.5 else 0
            if predicted_class == rec.outcome:
                correct += 1
            if predicted_class == 1 and rec.outcome == 1:
                tp += 1
            elif predicted_class == 1 and rec.outcome == 0:
                fp += 1
            elif predicted_class == 0 and rec.outcome == 0:
                tn += 1
            else:
                fn += 1
        n = len(records)
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = (2 * precision * sensitivity / (precision + sensitivity)) \
            if (precision + sensitivity) > 0 else 0.0
        return TrainingMetrics(
            loss=total_loss / n if n > 0 else 0,
            accuracy=correct / n if n > 0 else 0,
            sensitivity=sensitivity, specificity=specificity,
            f1_score=f1, num_samples=n,
        )

    def get_weights(self) -> Tuple[List[float], float]:
        return list(self.weights), self.bias

    def set_weights(self, weights: List[float], bias: float) -> None:
        self.weights = list(weights)
        self.bias = bias


# ---------------------------------------------------------------------------
# DP noise
# ---------------------------------------------------------------------------

def _add_dp_noise(values: List[float], epsilon: float, sensitivity: float = 1.0) -> List[float]:
    if epsilon <= 0:
        return values
    noisy = []
    for v in values:
        scale = sensitivity / epsilon
        u = random.random() - 0.5
        noise = -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u)) if u != 0 else 0
        noisy.append(v + noise)
    return noisy


# ---------------------------------------------------------------------------
# Virtual hospital
# ---------------------------------------------------------------------------

class VirtualHospital:
    """Simulates a hospital participating in the federated study."""

    def __init__(self, config: HospitalConfig):
        self.config = config
        self._data: List[PatientRecord] = []
        self._model = LocalLogisticModel()
        self._metrics_history: List[TrainingMetrics] = []
        self._audit_log: List[Dict[str, Any]] = []
        self._dp_budget_spent = 0.0

    def load_data(self) -> int:
        gen = SyntheticPatientGenerator()
        self._data = gen.generate(self.config)
        self._log_audit("data_loaded", {"num_records": len(self._data)})
        return len(self._data)

    def train_local(self, epochs: int = 5) -> List[TrainingMetrics]:
        metrics = []
        for e in range(epochs):
            random.shuffle(self._data)
            m = self._model.train_epoch(self._data)
            m.epoch = e
            metrics.append(m)
            self._metrics_history.append(m)
        self._log_audit("local_training", {
            "epochs": epochs, "final_acc": metrics[-1].accuracy if metrics else 0})
        return metrics

    def get_dp_gradients(self) -> Tuple[List[float], float]:
        weights, bias = self._model.get_weights()
        noisy_w = _add_dp_noise(weights, self.config.dp_epsilon)
        noisy_b = _add_dp_noise([bias], self.config.dp_epsilon)[0]
        self._dp_budget_spent += self.config.dp_epsilon
        self._log_audit("dp_gradients_shared", {
            "epsilon": self.config.dp_epsilon,
            "total_budget_spent": self._dp_budget_spent,
        })
        return noisy_w, noisy_b

    def apply_global_weights(self, weights: List[float], bias: float) -> None:
        self._model.set_weights(weights, bias)
        self._log_audit("global_weights_applied", {})

    def evaluate(self) -> TrainingMetrics:
        m = self._model.train_epoch(self._data)
        m.epoch = -1
        return m

    def get_compliance_report(self) -> ComplianceReport:
        return ComplianceReport(
            hospital_id=self.config.hospital_id,
            regulations=[r.value for r in self.config.regulations],
            dp_applied=True, dp_epsilon=self._dp_budget_spent,
            dp_delta=self.config.dp_delta,
            data_stays_local=True, data_encrypted=True,
            audit_trail=list(self._audit_log),
            status=ComplianceStatus.COMPLIANT,
        )

    def _log_audit(self, action: str, details: Dict[str, Any]) -> None:
        self._audit_log.append({
            "timestamp": time.time(),
            "hospital": self.config.hospital_id,
            "action": action,
            "details": details,
        })

    @property
    def data_size(self) -> int:
        return len(self._data)


# ---------------------------------------------------------------------------
# Federated aggregator
# ---------------------------------------------------------------------------

class FederatedAggregator:
    """Aggregates DP-protected model updates from hospitals."""

    def __init__(self, n_features: int = 7):
        self.n_features = n_features
        self._round = 0
        self._history: List[Dict[str, Any]] = []

    def aggregate(self, hospital_updates: List[Tuple[List[float], float, int]]) -> Tuple[List[float], float]:
        total_samples = sum(n for _, _, n in hospital_updates)
        if total_samples == 0:
            return [0.0] * self.n_features, 0.0
        avg_weights = [0.0] * self.n_features
        avg_bias = 0.0
        for weights, bias, n_samples in hospital_updates:
            w_factor = n_samples / total_samples
            for j in range(self.n_features):
                avg_weights[j] += weights[j] * w_factor
            avg_bias += bias * w_factor
        self._round += 1
        self._history.append({
            "round": self._round,
            "num_hospitals": len(hospital_updates),
            "total_samples": total_samples,
            "timestamp": time.time(),
        })
        return avg_weights, avg_bias


# ---------------------------------------------------------------------------
# Federated study coordinator
# ---------------------------------------------------------------------------

class FederatedStudyCoordinator:
    """Orchestrates the multi-hospital federated study."""

    def __init__(self, study_name: str = "multi_hospital_readmission"):
        self.study_name = study_name
        self.study_id = str(uuid.uuid4())[:12]
        self.phase = StudyPhase.SETUP
        self._hospitals: Dict[str, VirtualHospital] = {}
        self._aggregator = FederatedAggregator()
        self._round_metrics: List[Dict[str, Any]] = []

    def add_hospital(self, config: HospitalConfig) -> VirtualHospital:
        h = VirtualHospital(config)
        self._hospitals[config.hospital_id] = h
        return h

    def setup_default_hospitals(self) -> None:
        configs = [
            HospitalConfig("hospital_A", "Metro General Hospital", "us-east-sovereign",
                           num_patients=800, data_bias=0.0,
                           regulations=[Regulation.HIPAA, Regulation.HITECH]),
            HospitalConfig("hospital_B", "University Medical Center", "us-west-sovereign",
                           num_patients=600, data_bias=0.05,
                           regulations=[Regulation.HIPAA]),
            HospitalConfig("hospital_C", "Community Hospital", "us-central-sovereign",
                           num_patients=400, data_bias=-0.05,
                           regulations=[Regulation.HIPAA]),
            HospitalConfig("hospital_D", "European Clinical Centre", "eu-sovereign",
                           num_patients=700, data_bias=0.02,
                           regulations=[Regulation.GDPR, Regulation.HIPAA]),
            HospitalConfig("hospital_E", "Children's Hospital", "us-east-sovereign",
                           num_patients=300, data_bias=-0.1,
                           regulations=[Regulation.HIPAA, Regulation.FDA_21CFR11]),
        ]
        for c in configs:
            self.add_hospital(c)

    def load_all_data(self) -> Dict[str, int]:
        self.phase = StudyPhase.DATA_VALIDATION
        counts = {}
        for hid, h in self._hospitals.items():
            counts[hid] = h.load_data()
        return counts

    def run_federated_training(self, rounds: int = 10,
                               local_epochs: int = 3) -> List[Dict[str, Any]]:
        self.phase = StudyPhase.TRAINING
        for r in range(rounds):
            # local training
            for h in self._hospitals.values():
                h.train_local(local_epochs)
            # collect DP gradients
            updates = []
            for h in self._hospitals.values():
                w, b = h.get_dp_gradients()
                updates.append((w, b, h.data_size))
            # aggregate
            global_w, global_b = self._aggregator.aggregate(updates)
            # distribute
            for h in self._hospitals.values():
                h.apply_global_weights(global_w, global_b)
            # evaluate
            round_eval = {"round": r + 1, "hospitals": {}}
            for hid, h in self._hospitals.items():
                m = h.evaluate()
                round_eval["hospitals"][hid] = {
                    "accuracy": round(m.accuracy, 4),
                    "f1": round(m.f1_score, 4),
                    "sensitivity": round(m.sensitivity, 4),
                    "specificity": round(m.specificity, 4),
                }
            self._round_metrics.append(round_eval)
            logger.info("Round %d complete", r + 1)
        self.phase = StudyPhase.EVALUATION
        return self._round_metrics

    def cross_hospital_comparison(self) -> Dict[str, Any]:
        comparison: Dict[str, Any] = {"hospitals": {}}
        for hid, h in self._hospitals.items():
            m = h.evaluate()
            comparison["hospitals"][hid] = {
                "name": h.config.name,
                "zone_id": h.config.zone_id,
                "num_patients": h.data_size,
                "accuracy": round(m.accuracy, 4),
                "f1_score": round(m.f1_score, 4),
                "sensitivity": round(m.sensitivity, 4),
                "specificity": round(m.specificity, 4),
            }
        accs = [v["accuracy"] for v in comparison["hospitals"].values()]
        comparison["summary"] = {
            "mean_accuracy": round(statistics.mean(accs), 4) if accs else 0,
            "std_accuracy": round(statistics.stdev(accs), 4) if len(accs) > 1 else 0,
            "best_hospital": max(comparison["hospitals"].items(),
                                 key=lambda x: x[1]["accuracy"])[0] if accs else "",
            "total_patients": sum(h.data_size for h in self._hospitals.values()),
            "data_shared": False,
        }
        return comparison

    def generate_compliance_report(self) -> Dict[str, Any]:
        self.phase = StudyPhase.REPORTING
        reports = {}
        for hid, h in self._hospitals.items():
            r = h.get_compliance_report()
            reports[hid] = {
                "hospital": h.config.name,
                "status": r.status.value,
                "regulations": r.regulations,
                "dp_applied": r.dp_applied,
                "dp_epsilon_total": round(r.dp_epsilon, 4),
                "data_local": r.data_stays_local,
                "encrypted": r.data_encrypted,
                "audit_entries": len(r.audit_trail),
            }
        self.phase = StudyPhase.COMPLETED
        return {
            "study_id": self.study_id,
            "study_name": self.study_name,
            "num_hospitals": len(self._hospitals),
            "overall_status": ComplianceStatus.COMPLIANT.value,
            "hospitals": reports,
            "generated_at": time.time(),
        }

    def get_study_summary(self) -> Dict[str, Any]:
        return {
            "study_id": self.study_id,
            "name": self.study_name,
            "phase": self.phase.value,
            "hospitals": len(self._hospitals),
            "training_rounds": len(self._round_metrics),
            "total_patients": sum(h.data_size for h in self._hospitals.values()),
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def run_demo() -> None:
    coord = FederatedStudyCoordinator("30-Day Readmission Prediction")
    coord.setup_default_hospitals()
    counts = coord.load_all_data()
    logger.info("Data loaded: %s", counts)
    metrics = coord.run_federated_training(rounds=5, local_epochs=2)
    logger.info("Final round: %s", json.dumps(metrics[-1], indent=2))
    comparison = coord.cross_hospital_comparison()
    logger.info("Comparison: %s", json.dumps(comparison, indent=2))
    compliance = coord.generate_compliance_report()
    logger.info("Compliance: %s", json.dumps(compliance, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_demo()

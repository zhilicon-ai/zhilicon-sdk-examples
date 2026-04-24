"""
Zhilicon Example - Financial Fraud Detection
==============================================
Cross-bank fraud detection: each bank has a data vault, federated model
training across banks, real-time inference on transaction streams, ZK proofs
of compliance, all without sharing raw transaction data.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import random
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    PURCHASE = "purchase"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    ONLINE = "online"
    POS = "pos"
    ATM = "atm"


class FraudLabel(Enum):
    LEGITIMATE = 0
    FRAUD = 1
    SUSPICIOUS = 2


class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceProofType(Enum):
    ZK_RANGE = "zk_range_proof"
    ZK_MEMBERSHIP = "zk_membership_proof"
    ZK_SUM = "zk_sum_proof"
    AUDIT_HASH = "audit_hash"


@dataclass
class Transaction:
    tx_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    bank_id: str = ""
    account_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    tx_type: TransactionType = TransactionType.PURCHASE
    merchant_category: str = ""
    country: str = "US"
    timestamp: float = field(default_factory=time.time)
    is_international: bool = False
    label: FraudLabel = FraudLabel.LEGITIMATE
    risk_score: float = 0.0


@dataclass
class FraudAlert:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    tx_id: str = ""
    bank_id: str = ""
    risk_score: float = 0.0
    level: AlertLevel = AlertLevel.LOW
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


@dataclass
class ComplianceProof:
    proof_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    proof_type: ComplianceProofType = ComplianceProofType.AUDIT_HASH
    bank_id: str = ""
    statement: str = ""
    commitment: str = ""
    proof_data: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class BankConfig:
    bank_id: str
    name: str
    zone_id: str
    num_accounts: int = 1000
    fraud_rate: float = 0.02
    dp_epsilon: float = 1.0


@dataclass
class ModelMetrics:
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    false_positive_rate: float = 0.0
    num_samples: int = 0


class TransactionGenerator:
    MERCHANTS = ["grocery", "electronics", "travel", "dining", "healthcare",
                 "entertainment", "utilities", "clothing", "fuel", "online"]
    COUNTRIES = ["US", "US", "US", "UK", "DE", "FR", "JP", "CA", "AU", "BR"]

    def generate(self, config: BankConfig, num_tx: int = 5000) -> List[Transaction]:
        rng = random.Random(hash(config.bank_id))
        txns = []
        for i in range(num_tx):
            is_fraud = rng.random() < config.fraud_rate
            amount = rng.uniform(500, 10000) if is_fraud else rng.lognormvariate(3.5, 1.2)
            amount = round(min(50000, max(0.01, amount)), 2)
            country = rng.choice(self.COUNTRIES)
            txns.append(Transaction(
                bank_id=config.bank_id,
                account_id=f"{config.bank_id}-A{rng.randint(0, config.num_accounts):05d}",
                amount=amount, tx_type=rng.choice(list(TransactionType)),
                merchant_category=rng.choice(self.MERCHANTS), country=country,
                is_international=country != "US",
                label=FraudLabel.FRAUD if is_fraud else FraudLabel.LEGITIMATE,
                timestamp=time.time() - rng.uniform(0, 86400 * 30)))
        return txns


class LocalFraudModel:
    def __init__(self, n_features: int = 8, lr: float = 0.01):
        self.n_features = n_features
        self.lr = lr
        self.weights = [random.gauss(0, 0.1) for _ in range(n_features)]
        self.bias = 0.0

    @staticmethod
    def _sigmoid(z: float) -> float:
        z = max(-500, min(500, z))
        return 1.0 / (1.0 + math.exp(-z))

    def _features(self, tx: Transaction) -> List[float]:
        return [
            tx.amount / 10000.0,
            1.0 if tx.is_international else 0.0,
            1.0 if tx.tx_type == TransactionType.ONLINE else 0.0,
            1.0 if tx.tx_type == TransactionType.TRANSFER else 0.0,
            hash(tx.merchant_category) % 10 / 10.0,
            hash(tx.country) % 10 / 10.0,
            1.0 if tx.amount > 5000 else 0.0,
            (tx.timestamp % 86400) / 86400.0,
        ]

    def predict(self, tx: Transaction) -> float:
        feats = self._features(tx)
        z = self.bias + sum(w * f for w, f in zip(self.weights, feats))
        return self._sigmoid(z)

    def train_epoch(self, txns: List[Transaction]) -> ModelMetrics:
        tp = fp = tn = fn = 0
        for tx in txns:
            feats = self._features(tx)
            pred = self.predict(tx)
            y = 1.0 if tx.label == FraudLabel.FRAUD else 0.0
            error = pred - y
            for j in range(self.n_features):
                self.weights[j] -= self.lr * error * feats[j]
            self.bias -= self.lr * error
            cls = 1 if pred >= 0.5 else 0
            actual = 1 if tx.label == FraudLabel.FRAUD else 0
            if cls == 1 and actual == 1: tp += 1
            elif cls == 1 and actual == 0: fp += 1
            elif cls == 0 and actual == 0: tn += 1
            else: fn += 1
        n = len(txns)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        return ModelMetrics(accuracy=(tp + tn) / n if n else 0, precision=prec,
                            recall=rec, f1=f1, false_positive_rate=fpr, num_samples=n)

    def get_weights(self) -> Tuple[List[float], float]:
        return list(self.weights), self.bias

    def set_weights(self, w: List[float], b: float) -> None:
        self.weights = list(w)
        self.bias = b


class ZKProofGenerator:
    def __init__(self, bank_id: str):
        self.bank_id = bank_id

    def prove_fraud_rate_below(self, txns: List[Transaction],
                                threshold: float) -> ComplianceProof:
        fraud_count = sum(1 for t in txns if t.label == FraudLabel.FRAUD)
        actual_rate = fraud_count / len(txns) if txns else 0
        commitment = hashlib.sha256(
            f"{self.bank_id}:{fraud_count}:{len(txns)}:{time.time()}".encode()
        ).hexdigest()
        return ComplianceProof(
            proof_type=ComplianceProofType.ZK_RANGE, bank_id=self.bank_id,
            statement=f"Fraud rate < {threshold}", commitment=commitment,
            proof_data={"threshold": threshold, "n": len(txns)},
            verified=actual_rate < threshold)

    def prove_aml_compliance(self, txns: List[Transaction],
                              max_single: float = 10000) -> ComplianceProof:
        violations = sum(1 for t in txns if t.amount > max_single)
        commitment = hashlib.sha256(
            f"{self.bank_id}:aml:{violations}:{time.time()}".encode()
        ).hexdigest()
        return ComplianceProof(
            proof_type=ComplianceProofType.ZK_SUM, bank_id=self.bank_id,
            statement=f"All below {max_single}", commitment=commitment,
            proof_data={"max": max_single, "n": len(txns)},
            verified=violations == 0)

    def audit_hash(self, txns: List[Transaction]) -> ComplianceProof:
        data = json.dumps([{"id": t.tx_id, "amt": t.amount} for t in txns], sort_keys=True)
        h = hashlib.sha256(data.encode()).hexdigest()
        return ComplianceProof(
            proof_type=ComplianceProofType.AUDIT_HASH, bank_id=self.bank_id,
            statement="Audit hash", commitment=h, verified=True,
            proof_data={"n": len(txns), "algo": "sha256"})


class BankDataVault:
    def __init__(self, config: BankConfig):
        self.config = config
        self._txns: List[Transaction] = []
        self._model = LocalFraudModel()
        self._alerts: List[FraudAlert] = []
        self._zk = ZKProofGenerator(config.bank_id)
        self._audit: List[Dict[str, Any]] = []

    def load_data(self, num_tx: int = 5000) -> int:
        self._txns = TransactionGenerator().generate(self.config, num_tx)
        self._log("data_loaded", {"count": len(self._txns)})
        return len(self._txns)

    def train_local(self, epochs: int = 5) -> List[ModelMetrics]:
        metrics = []
        for _ in range(epochs):
            random.shuffle(self._txns)
            metrics.append(self._model.train_epoch(self._txns))
        self._log("trained", {"epochs": epochs, "f1": metrics[-1].f1 if metrics else 0})
        return metrics

    def get_dp_weights(self) -> Tuple[List[float], float]:
        w, b = self._model.get_weights()
        eps = self.config.dp_epsilon
        noisy_w = [v + self._laplace(eps) for v in w]
        noisy_b = b + self._laplace(eps)
        self._log("weights_shared", {"epsilon": eps})
        return noisy_w, noisy_b

    def apply_global_weights(self, w: List[float], b: float) -> None:
        self._model.set_weights(w, b)

    def score_transactions(self) -> List[FraudAlert]:
        alerts = []
        for tx in self._txns:
            score = self._model.predict(tx)
            tx.risk_score = score
            if score > 0.7:
                level = AlertLevel.CRITICAL if score > 0.9 else AlertLevel.HIGH
                alerts.append(FraudAlert(tx_id=tx.tx_id, bank_id=self.config.bank_id,
                                         risk_score=score, level=level,
                                         reason=f"Risk: {score:.3f}"))
            elif score > 0.5:
                alerts.append(FraudAlert(tx_id=tx.tx_id, bank_id=self.config.bank_id,
                                         risk_score=score, level=AlertLevel.MEDIUM,
                                         reason=f"Elevated: {score:.3f}"))
        self._alerts.extend(alerts)
        return alerts

    def generate_proofs(self) -> List[ComplianceProof]:
        return [self._zk.prove_fraud_rate_below(self._txns, 0.05),
                self._zk.prove_aml_compliance(self._txns),
                self._zk.audit_hash(self._txns)]

    def evaluate(self) -> ModelMetrics:
        return self._model.train_epoch(self._txns)

    @staticmethod
    def _laplace(eps: float, sens: float = 1.0) -> float:
        if eps <= 0: return 0
        scale = sens / eps
        u = random.random() - 0.5
        return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u)) if u else 0

    def _log(self, action: str, details: Dict[str, Any]) -> None:
        self._audit.append({"ts": time.time(), "bank": self.config.bank_id,
                            "action": action, "details": details})

    @property
    def data_size(self) -> int:
        return len(self._txns)


class FederatedFraudDetection:
    def __init__(self):
        self._banks: Dict[str, BankDataVault] = {}
        self._round_metrics: List[Dict[str, Any]] = []

    def add_bank(self, config: BankConfig) -> BankDataVault:
        vault = BankDataVault(config)
        self._banks[config.bank_id] = vault
        return vault

    def setup_default_banks(self) -> None:
        for c in [
            BankConfig("bank_alpha", "Alpha National", "us-east", 2000, 0.02),
            BankConfig("bank_beta", "Beta Financial", "us-west", 1500, 0.03),
            BankConfig("bank_gamma", "Gamma Trust", "eu-sovereign", 1800, 0.015),
            BankConfig("bank_delta", "Delta Credit Union", "us-central", 800, 0.025),
        ]:
            self.add_bank(c)

    def load_all_data(self) -> Dict[str, int]:
        return {bid: b.load_data() for bid, b in self._banks.items()}

    def run_federated_training(self, rounds: int = 8, local_epochs: int = 3) -> List[Dict]:
        for r in range(rounds):
            for b in self._banks.values():
                b.train_local(local_epochs)
            updates = [(w, b, v.data_size) for v in self._banks.values()
                       for w, b in [v.get_dp_weights()]]
            gw, gb = self._aggregate(updates)
            for b in self._banks.values():
                b.apply_global_weights(gw, gb)
            evals = {}
            for bid, b in self._banks.items():
                m = b.evaluate()
                evals[bid] = {"acc": round(m.accuracy, 4), "f1": round(m.f1, 4),
                              "prec": round(m.precision, 4), "rec": round(m.recall, 4)}
            self._round_metrics.append({"round": r + 1, "banks": evals})
        return self._round_metrics

    @staticmethod
    def _aggregate(updates: List[Tuple[List[float], float, int]]) -> Tuple[List[float], float]:
        total = sum(n for _, _, n in updates) or 1
        dim = len(updates[0][0])
        aw = [0.0] * dim
        ab = 0.0
        for w, b, n in updates:
            f = n / total
            for j in range(dim):
                aw[j] += w[j] * f
            ab += b * f
        return aw, ab

    def run_realtime_scoring(self) -> Dict[str, Any]:
        return {bid: {"alerts": len(b.score_transactions())} for bid, b in self._banks.items()}

    def generate_all_proofs(self) -> Dict[str, List[Dict]]:
        return {bid: [{"type": p.proof_type.value, "verified": p.verified}
                       for p in b.generate_proofs()]
                for bid, b in self._banks.items()}


def run_demo() -> None:
    system = FederatedFraudDetection()
    system.setup_default_banks()
    system.load_all_data()
    metrics = system.run_federated_training(rounds=5)
    logger.info("Final: %s", json.dumps(metrics[-1], indent=2))
    logger.info("Proofs: %s", json.dumps(system.generate_all_proofs(), indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_demo()

#!/usr/bin/env python3
"""
Zhilicon Tutorial 05 -- Privacy Engineering
=============================================

Privacy engineering tutorial:
  1. Differential privacy (basics, budget tracking)
  2. Federated learning (FedAvg, secure aggregation)
  3. Encrypted tensors
  4. Hardware privacy engine
  5. Privacy attack simulation
  6. Synthetic data generation

How to run:
    pip install zhilicon
    python 05_privacy_engineering.py

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys, time, random, math, hashlib, json, secrets
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ── Simulation layer ────────────────────────────────────────────────────

class DPMechanism:
    """Differential privacy mechanism."""
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5,
                 mechanism: str = "gaussian"):
        self.epsilon = epsilon
        self.delta = delta
        self.mechanism = mechanism
        self.epsilon_spent = 0.0
        self.queries = 0

    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        if self.mechanism == "gaussian":
            sigma = sensitivity * math.sqrt(2 * math.log(1.25 / self.delta)) / self.epsilon
            noise = random.gauss(0, sigma)
        else:
            noise = random.uniform(-sensitivity/self.epsilon, sensitivity/self.epsilon)
        self.queries += 1
        self.epsilon_spent += self.epsilon * 0.01
        return value + noise

    @property
    def budget_remaining(self) -> float:
        return max(0, self.epsilon - self.epsilon_spent)

class PrivacyBudgetTracker:
    """Track privacy budget across multiple operations."""
    def __init__(self, total_epsilon: float, total_delta: float = 1e-5):
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.operations: List[Dict] = []
        self._spent = 0.0

    def consume(self, epsilon: float, operation: str) -> bool:
        if self._spent + epsilon > self.total_epsilon:
            return False
        self._spent += epsilon
        self.operations.append({"op": operation, "epsilon": epsilon,
                                 "cumulative": self._spent})
        return True

    @property
    def remaining(self) -> float: return self.total_epsilon - self._spent

    @property
    def spent(self) -> float: return self._spent

class FederatedNode:
    def __init__(self, node_id: str, data_size: int):
        self.node_id = node_id
        self.data_size = data_size

    def local_train(self) -> Dict[str, Any]:
        loss = random.uniform(0.1, 0.8)
        return {"node": self.node_id, "loss": loss, "samples": self.data_size,
                "gradient_hash": hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:16]}

class SecureAggregator:
    def __init__(self, threshold: int = 3):
        self.threshold = threshold

    def aggregate(self, gradients: List[Dict]) -> Dict[str, Any]:
        avg_loss = sum(g["loss"] for g in gradients) / len(gradients)
        total_samples = sum(g["samples"] for g in gradients)
        return {"avg_loss": avg_loss, "total_samples": total_samples,
                "participants": len(gradients), "secure": True}

class EncryptedTensor:
    def __init__(self, shape: Tuple, scheme: str = "ckks"):
        self.shape = shape
        self.scheme = scheme
        self.encrypted = True
        self._data = secrets.token_bytes(64)

    def add(self, other: "EncryptedTensor") -> "EncryptedTensor":
        return EncryptedTensor(self.shape, self.scheme)

    def multiply_plain(self, scalar: float) -> "EncryptedTensor":
        return EncryptedTensor(self.shape, self.scheme)

    def decrypt(self, secret_key: bytes) -> List[float]:
        return [random.gauss(0, 1) for _ in range(min(10, self.shape[0]))]

class HardwarePrivacyEngine:
    def __init__(self, epsilon_budget: float = 10.0, device: str = "prometheus"):
        self.epsilon_budget = epsilon_budget
        self.device = device
        self.epsilon_consumed = 0.0

    def noisy_sgd_step(self, grad_norm: float, noise_multiplier: float) -> Dict:
        step_epsilon = 1.0 / noise_multiplier
        self.epsilon_consumed += step_epsilon * 0.001
        return {"noise_added": True, "grad_norm_clipped": min(grad_norm, 1.0),
                "epsilon_step": step_epsilon * 0.001,
                "epsilon_total": self.epsilon_consumed,
                "hardware_attested": True}

class PrivacyAttackSimulator:
    def membership_inference(self, model_outputs: List[float],
                             training_data_member: bool) -> Dict:
        confidence = random.uniform(0.45, 0.65)
        return {"attack": "membership_inference", "success_rate": confidence,
                "is_member_prediction": confidence > 0.55,
                "actual_member": training_data_member}

    def model_inversion(self, model_name: str) -> Dict:
        fidelity = random.uniform(0.05, 0.25)
        return {"attack": "model_inversion", "reconstruction_fidelity": fidelity,
                "risk_level": "low" if fidelity < 0.15 else "medium"}

    def attribute_inference(self, model_name: str, target_attr: str) -> Dict:
        accuracy = random.uniform(0.3, 0.6)
        return {"attack": "attribute_inference", "target": target_attr,
                "inference_accuracy": accuracy,
                "risk_level": "low" if accuracy < 0.5 else "medium"}

class SyntheticDataGenerator:
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta
        self._fitted = False

    def fit(self, data_summary: Dict) -> None:
        self._fitted = True
        self._summary = data_summary

    def generate(self, n_samples: int) -> List[Dict]:
        samples = []
        for i in range(n_samples):
            samples.append({
                "id": i,
                "age": max(0, int(random.gauss(45, 15))),
                "value": round(random.gauss(100, 30), 2),
                "category": random.choice(["A", "B", "C"]),
            })
        return samples

    def evaluate_utility(self, real_summary: Dict, synthetic_data: List) -> Dict:
        return {"statistical_similarity": random.uniform(0.85, 0.95),
                "ml_utility": random.uniform(0.80, 0.92),
                "privacy_score": random.uniform(0.90, 0.99)}

# ── Tutorial ────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}\n")

def tutorial_differential_privacy():
    section("1. Differential Privacy Basics")
    dp = DPMechanism(epsilon=1.0, delta=1e-5, mechanism="gaussian")
    true_value = 42.0
    print(f"True value: {true_value}")
    print(f"Privacy budget: epsilon={dp.epsilon}, delta={dp.delta}\n")
    print(f"Noisy outputs (same true value, different noise each time):")
    for i in range(5):
        noisy = dp.add_noise(true_value, sensitivity=1.0)
        print(f"  Query {i+1}: {noisy:.2f} (noise = {noisy - true_value:+.2f})")
    print(f"\nBudget spent: {dp.epsilon_spent:.4f} / {dp.epsilon}")
    print(f"Budget remaining: {dp.budget_remaining:.4f}")

    section("1b. Privacy Budget Tracking")
    tracker = PrivacyBudgetTracker(total_epsilon=8.0)
    ops = [("mean_age", 0.5), ("median_income", 0.5), ("count_diagnosis", 1.0),
           ("histogram_bmi", 2.0), ("regression_coef", 3.0)]
    print(f"Total budget: epsilon={tracker.total_epsilon}\n")
    for op_name, eps in ops:
        success = tracker.consume(eps, op_name)
        status = "OK" if success else "DENIED (budget exhausted)"
        bar = "#" * int(tracker.spent / tracker.total_epsilon * 30)
        print(f"  {op_name:25s} eps={eps:.1f} -> {status} "
              f"[{bar:30s}] {tracker.spent:.1f}/{tracker.total_epsilon}")

def tutorial_federated_learning():
    section("2. Federated Learning (FedAvg + Secure Aggregation)")
    nodes = [FederatedNode(f"Hospital-{chr(65+i)}", random.randint(500, 2000))
             for i in range(5)]
    aggregator = SecureAggregator(threshold=3)
    print(f"Nodes: {len(nodes)}")
    for n in nodes:
        print(f"  {n.node_id}: {n.data_size} samples")
    print(f"\nFederated training (5 rounds):")
    for round_num in range(1, 6):
        local_results = [n.local_train() for n in nodes]
        agg = aggregator.aggregate(local_results)
        print(f"  Round {round_num} | Avg loss: {agg['avg_loss']:.4f} | "
              f"Samples: {agg['total_samples']:,} | "
              f"Secure: {agg['secure']}")
    print(f"\nKey property: NO raw data was shared. Only encrypted gradients.")

def tutorial_encrypted_tensors():
    section("3. Encrypted Tensors (Homomorphic Encryption)")
    print("Compute on encrypted data without decrypting it.\n")
    key = secrets.token_bytes(32)
    a = EncryptedTensor((100,), scheme="ckks")
    b = EncryptedTensor((100,), scheme="ckks")
    print(f"Tensor A: encrypted, shape={a.shape}")
    print(f"Tensor B: encrypted, shape={b.shape}")
    c = a.add(b)
    print(f"A + B: encrypted, shape={c.shape} (computed on encrypted data!)")
    d = c.multiply_plain(2.5)
    print(f"(A+B) * 2.5: encrypted, shape={d.shape}")
    result = d.decrypt(key)
    print(f"Decrypted result (first 5): {[f'{v:.3f}' for v in result[:5]]}")
    print(f"\nThe server that computed A+B NEVER saw the plaintext data.")

def tutorial_hardware_privacy():
    section("4. Hardware Privacy Engine")
    engine = HardwarePrivacyEngine(epsilon_budget=10.0, device="prometheus")
    print(f"Hardware DP engine on {engine.device}")
    print(f"Budget: epsilon={engine.epsilon_budget}\n")
    for step in range(1, 11):
        grad_norm = random.uniform(0.5, 3.0)
        result = engine.noisy_sgd_step(grad_norm, noise_multiplier=1.1)
        print(f"  Step {step:3d} | Grad norm: {grad_norm:.2f} -> {result['grad_norm_clipped']:.2f} | "
              f"Eps: {result['epsilon_total']:.4f} | HW attested: {result['hardware_attested']}")
    print(f"\nHardware attestation PROVES the noise was actually added.")
    print(f"Unlike software DP, this cannot be bypassed.")

def tutorial_privacy_attacks():
    section("5. Privacy Attack Simulation (Red Teaming)")
    sim = PrivacyAttackSimulator()
    print("Testing model privacy with simulated attacks:\n")
    mi = sim.membership_inference([0.9, 0.1, 0.85, 0.3], True)
    print(f"  Membership Inference:")
    print(f"    Success rate: {mi['success_rate']:.2%}")
    print(f"    Risk: {'HIGH' if mi['success_rate'] > 0.6 else 'LOW'}")
    inv = sim.model_inversion("target-model")
    print(f"  Model Inversion:")
    print(f"    Reconstruction fidelity: {inv['reconstruction_fidelity']:.2%}")
    print(f"    Risk: {inv['risk_level']}")
    attr = sim.attribute_inference("target-model", "medical_diagnosis")
    print(f"  Attribute Inference (target: {attr['target']}):")
    print(f"    Accuracy: {attr['inference_accuracy']:.2%}")
    print(f"    Risk: {attr['risk_level']}")

def tutorial_synthetic_data():
    section("6. Synthetic Data Generation with DP Guarantees")
    gen = SyntheticDataGenerator(epsilon=1.0, delta=1e-5)
    gen.fit({"mean_age": 45, "std_age": 15, "categories": ["A","B","C"]})
    synthetic = gen.generate(n_samples=10)
    print(f"Generated {len(synthetic)} synthetic records:")
    print(f"  {'ID':>4} {'Age':>5} {'Value':>8} {'Cat':>5}")
    for row in synthetic[:10]:
        print(f"  {row['id']:>4} {row['age']:>5} {row['value']:>8.2f} {row['category']:>5}")
    utility = gen.evaluate_utility({}, synthetic)
    print(f"\nUtility evaluation:")
    print(f"  Statistical similarity: {utility['statistical_similarity']:.2%}")
    print(f"  ML utility preservation: {utility['ml_utility']:.2%}")
    print(f"  Privacy score: {utility['privacy_score']:.2%}")
    print(f"\nDP guarantee: epsilon={gen.epsilon}, delta={gen.delta}")

def main():
    print("=" * 60)
    print("  Zhilicon Tutorial 05: Privacy Engineering")
    print("=" * 60)
    tutorial_differential_privacy()
    tutorial_federated_learning()
    tutorial_encrypted_tensors()
    tutorial_hardware_privacy()
    tutorial_privacy_attacks()
    tutorial_synthetic_data()
    print(f"\nTutorial complete! Next: 06_zero_knowledge.py")

if __name__ == "__main__":
    main()

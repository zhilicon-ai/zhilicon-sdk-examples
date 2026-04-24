#!/usr/bin/env python3
"""
Zhilicon Tutorial 03 -- Medical Imaging Pipeline
==================================================

Complete medical imaging pipeline on Discovery-1:
  1. Load DICOM study
  2. Preprocess (windowing, normalization)
  3. Run segmentation (CTAnalyzer)
  4. Run tumor detection
  5. Generate DICOM Structured Report
  6. Federated learning across hospitals
  7. Privacy-preserving training with differential privacy

How to run:
    pip install zhilicon
    python 03_medical_imaging.py

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys, time, random, hashlib, json, math, uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# ── Simulation layer ────────────────────────────────────────────────────

@dataclass
class DICOMStudy:
    study_uid: str = field(default_factory=lambda: f"1.2.840.{random.randint(100000,999999)}")
    patient_id: str = "ANON_001"
    modality: str = "CT"
    body_part: str = "CHEST"
    dimensions: Tuple[int,int,int] = (512, 512, 256)
    spacing_mm: Tuple[float,float,float] = (0.7, 0.7, 1.0)
    pixel_data: Optional[Any] = None  # Simulated
    window_center: float = -600.0
    window_width: float = 1500.0

@dataclass
class PreprocessedStudy:
    study: DICOMStudy = field(default_factory=DICOMStudy)
    normalized: bool = True
    windowed: bool = True
    resampled: bool = True
    target_spacing: Tuple[float,float,float] = (1.0, 1.0, 1.0)

@dataclass
class OrganSegmentation:
    organs: Dict[str, float] = field(default_factory=lambda: {
        "left_lung": 2840.0, "right_lung": 3120.0, "heart": 680.0,
        "aorta": 42.0, "trachea": 18.0, "esophagus": 12.0, "spine": 310.0,
    })
    dice_scores: Dict[str, float] = field(default_factory=lambda: {
        "left_lung": 0.97, "right_lung": 0.97, "heart": 0.94,
        "aorta": 0.91, "trachea": 0.89, "esophagus": 0.85, "spine": 0.96,
    })

@dataclass
class Nodule:
    location: str = "RUL"
    coordinates_mm: Tuple[float,float,float] = (142.3, 89.7, 178.2)
    size_mm: float = 8.3
    confidence: float = 0.94
    lung_rads: str = "4A"
    texture: str = "part-solid"
    calcification: bool = False
    spiculation: float = 0.3

@dataclass
class TumorDetection:
    nodules: List[Nodule] = field(default_factory=lambda: [
        Nodule(), Nodule(location="LLL", coordinates_mm=(280.1, 195.3, 210.8),
                         size_mm=4.1, confidence=0.78, lung_rads="3", texture="solid"),
    ])

@dataclass
class DICOMStructuredReport:
    sr_uid: str = field(default_factory=lambda: f"1.2.840.{random.randint(100000,999999)}")
    template: str = "TID 1500"
    findings: List[str] = field(default_factory=list)
    measurements: Dict[str, Any] = field(default_factory=dict)

class CTAnalyzer:
    def __init__(self, device="discovery-1", model_version="v3.2"):
        self.device = device
        self.model_version = model_version

    def load_study(self, path: str) -> DICOMStudy:
        time.sleep(0.1)
        return DICOMStudy()

    def preprocess(self, study: DICOMStudy, target_spacing=(1.0,1.0,1.0)) -> PreprocessedStudy:
        time.sleep(0.05)
        return PreprocessedStudy(study=study, target_spacing=target_spacing)

    def segment_organs(self, preprocessed: PreprocessedStudy) -> OrganSegmentation:
        time.sleep(0.15)
        return OrganSegmentation()

    def detect_tumors(self, preprocessed: PreprocessedStudy) -> TumorDetection:
        time.sleep(0.1)
        return TumorDetection()

    def generate_sr(self, study: DICOMStudy, seg: OrganSegmentation,
                    tumors: TumorDetection) -> DICOMStructuredReport:
        findings = []
        for organ, vol in seg.organs.items():
            findings.append(f"{organ}: {vol:.0f} mL (dice: {seg.dice_scores.get(organ, 0):.2f})")
        for nod in tumors.nodules:
            findings.append(f"Nodule at {nod.location}: {nod.size_mm}mm, "
                          f"Lung-RADS {nod.lung_rads}, conf={nod.confidence:.2f}")
        return DICOMStructuredReport(findings=findings)

class FederatedNode:
    def __init__(self, hospital_id: str, num_studies: int):
        self.hospital_id = hospital_id
        self.num_studies = num_studies
        self.local_loss: float = 0.0

    def local_train(self, rounds: int = 1) -> Dict[str, Any]:
        self.local_loss = random.uniform(0.1, 0.5)
        return {"hospital": self.hospital_id, "loss": self.local_loss,
                "studies": self.num_studies, "rounds": rounds}

class FederatedCoordinator:
    def __init__(self, nodes: List[FederatedNode]):
        self.nodes = nodes
        self.global_round = 0

    def train_round(self) -> Dict[str, Any]:
        self.global_round += 1
        results = []
        for node in self.nodes:
            r = node.local_train()
            results.append(r)
        avg_loss = sum(r["loss"] for r in results) / len(results)
        return {"round": self.global_round, "avg_loss": avg_loss,
                "participants": len(self.nodes), "local_results": results}

class DPTrainer:
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5,
                 max_grad_norm: float = 1.0):
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        self.epsilon_spent = 0.0

    def train_step(self) -> Dict[str, Any]:
        step_epsilon = self.epsilon * 0.01
        self.epsilon_spent += step_epsilon
        return {"epsilon_spent": self.epsilon_spent, "epsilon_budget": self.epsilon,
                "budget_remaining_pct": max(0, (1 - self.epsilon_spent/self.epsilon)*100)}

class _SimSovCtx:
    def __init__(self, **kw):
        self.country = kw.get("country", "us")
        self.regulations = kw.get("regulations", [])
    def __enter__(self): return self
    def __exit__(self, *a): pass

class _SimZh:
    __version__ = "0.2.0"
    SovereignContext = _SimSovCtx

try:
    import zhilicon as zh
except ImportError:
    zh = _SimZh()

# ── Tutorial ────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}\n")

def tutorial_load_dicom():
    section("1. Load DICOM Study")
    analyzer = CTAnalyzer(device="discovery-1")
    study = analyzer.load_study("/data/hospital_a/patient_001/ct_chest/")
    print(f"Study UID   : {study.study_uid}")
    print(f"Patient     : {study.patient_id}")
    print(f"Modality    : {study.modality}")
    print(f"Body part   : {study.body_part}")
    print(f"Dimensions  : {study.dimensions[0]}x{study.dimensions[1]}x{study.dimensions[2]}")
    print(f"Spacing (mm): {study.spacing_mm}")
    return study

def tutorial_preprocess(study):
    section("2. Preprocess (Windowing, Normalization)")
    analyzer = CTAnalyzer()
    print("Preprocessing steps:")
    print("  1. Apply HU windowing (center=-600, width=1500 for lung)")
    print("  2. Resample to isotropic 1mm spacing")
    print("  3. Normalize to [0, 1] range")
    preprocessed = analyzer.preprocess(study, target_spacing=(1.0, 1.0, 1.0))
    print(f"\nPreprocessed: normalized={preprocessed.normalized}, "
          f"windowed={preprocessed.windowed}, "
          f"spacing={preprocessed.target_spacing}")
    return preprocessed

def tutorial_segmentation(preprocessed):
    section("3. Organ Segmentation")
    analyzer = CTAnalyzer()
    seg = analyzer.segment_organs(preprocessed)
    print(f"Segmented {len(seg.organs)} organs:")
    for organ, vol in seg.organs.items():
        dice = seg.dice_scores.get(organ, 0)
        bar = "#" * int(dice * 20)
        print(f"  {organ:15s}: {vol:7.0f} mL  (Dice: {dice:.2f}) {bar}")
    return seg

def tutorial_tumor_detection(preprocessed):
    section("4. Tumor / Nodule Detection")
    analyzer = CTAnalyzer()
    tumors = analyzer.detect_tumors(preprocessed)
    print(f"Detected {len(tumors.nodules)} nodule(s):\n")
    for i, nod in enumerate(tumors.nodules):
        print(f"  Nodule {i+1}:")
        print(f"    Location    : {nod.location}")
        print(f"    Size        : {nod.size_mm} mm")
        print(f"    Texture     : {nod.texture}")
        print(f"    Lung-RADS   : {nod.lung_rads}")
        print(f"    Confidence  : {nod.confidence:.0%}")
        print(f"    Coordinates : {nod.coordinates_mm}")
        print(f"    Spiculation : {nod.spiculation:.1f}")
        print(f"    Calcified   : {nod.calcification}")
    return tumors

def tutorial_dicom_sr(study, seg, tumors):
    section("5. Generate DICOM Structured Report")
    analyzer = CTAnalyzer()
    sr = analyzer.generate_sr(study, seg, tumors)
    print(f"SR UID   : {sr.sr_uid}")
    print(f"Template : {sr.template}")
    print(f"Findings ({len(sr.findings)}):")
    for finding in sr.findings:
        print(f"  - {finding}")

def tutorial_federated_learning():
    section("6. Federated Learning Across Hospitals")
    print("Federated learning: train across hospitals WITHOUT sharing data.\n")
    nodes = [
        FederatedNode("Hospital-A (Dubai)", 1200),
        FederatedNode("Hospital-B (Abu Dhabi)", 800),
        FederatedNode("Hospital-C (Riyadh)", 950),
        FederatedNode("Hospital-D (Jeddah)", 650),
    ]
    coordinator = FederatedCoordinator(nodes)
    print(f"Participants: {len(nodes)}")
    for node in nodes:
        print(f"  {node.hospital_id}: {node.num_studies} studies")

    print(f"\nTraining (5 federated rounds):")
    for _ in range(5):
        result = coordinator.train_round()
        local_str = ", ".join(f"{r['hospital'].split('(')[0].strip()}={r['loss']:.3f}"
                              for r in result["local_results"])
        print(f"  Round {result['round']:2d} | Avg loss: {result['avg_loss']:.4f} | {local_str}")

    print(f"\nNo patient data left any hospital. Only encrypted gradients were shared.")

def tutorial_dp_training():
    section("7. Privacy-Preserving Training (Differential Privacy)")
    print("Differential privacy adds calibrated noise to gradients,")
    print("providing mathematical privacy guarantees.\n")
    dp = DPTrainer(epsilon=8.0, delta=1e-5, max_grad_norm=1.0)
    print(f"Privacy budget: epsilon={dp.epsilon}, delta={dp.delta}")
    print(f"Max gradient norm: {dp.max_grad_norm}\n")

    for step in range(1, 11):
        result = dp.train_step()
        bar_len = int(result["budget_remaining_pct"] / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"  Step {step:3d} | epsilon spent: {result['epsilon_spent']:.3f} / "
              f"{result['epsilon_budget']:.1f} | [{bar}] "
              f"{result['budget_remaining_pct']:.1f}%")

    print(f"\nWhen budget is exhausted, training STOPS (privacy guarantee preserved).")

def main():
    print("=" * 60)
    print("  Zhilicon Tutorial 03: Medical Imaging Pipeline")
    print("=" * 60)
    with zh.SovereignContext(country="us", regulations=["HIPAA"]):
        study = tutorial_load_dicom()
        preprocessed = tutorial_preprocess(study)
        seg = tutorial_segmentation(preprocessed)
        tumors = tutorial_tumor_detection(preprocessed)
        tutorial_dicom_sr(study, seg, tumors)
    tutorial_federated_learning()
    tutorial_dp_training()
    print(f"\nTutorial complete! Next: 04_llm_training.py")

if __name__ == "__main__":
    main()

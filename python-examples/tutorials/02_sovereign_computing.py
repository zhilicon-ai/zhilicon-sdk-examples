#!/usr/bin/env python3
"""
Zhilicon Tutorial 02 -- Sovereign Computing Deep Dive
======================================================

A comprehensive guide to Zhilicon's sovereignty system.
This is what makes Zhilicon UNIQUE -- no other chip platform has this.

Topics covered:
  1. SovereignContext -- basic, nested, composable
  2. SovereignPolicy -- presets and custom policies
  3. Attestation -- request, verify, export hardware proofs
  4. AuditLog -- tamper-proof operation logging
  5. DataResidency -- all supported regions
  6. DataClassification -- PUBLIC through SOVEREIGN_SECRET

How to run:
    pip install zhilicon
    python 02_sovereign_computing.py

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys
import time
import random
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from enum import Enum

# ── Simulation layer ────────────────────────────────────────────────────

class DataResidency(Enum):
    UAE = "ae"
    SAUDI_ARABIA = "sa"
    UNITED_STATES = "us"
    EUROPEAN_UNION = "eu"
    INDIA = "in_"
    SINGAPORE = "sg"
    JAPAN = "jp"
    SOUTH_KOREA = "kr"
    UNITED_KINGDOM = "gb"
    GERMANY = "de"
    FRANCE = "fr"
    BRAZIL = "br"
    CANADA = "ca"
    AUSTRALIA = "au"

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"
    SOVEREIGN_SECRET = "sovereign_secret"

class EncryptionStandard(Enum):
    AES_128_GCM = "aes-128-gcm"
    AES_256_GCM = "aes-256-gcm"
    CHACHA20_POLY1305 = "chacha20-poly1305"

class KeyManagement(Enum):
    PLATFORM_MANAGED = "platform"
    HARDWARE_GENERATED = "hardware"
    CUSTOMER_MANAGED = "customer"

@dataclass
class SovereignPolicy:
    """Configurable sovereignty policy."""
    residency: DataResidency = DataResidency.UAE
    classification: DataClassification = DataClassification.CONFIDENTIAL
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True
    encryption_standard: EncryptionStandard = EncryptionStandard.AES_256_GCM
    key_management: KeyManagement = KeyManagement.HARDWARE_GENERATED
    attestation: bool = True
    audit: bool = True
    data_never_crosses_border: bool = True
    max_data_retention_days: int = 365
    allowed_operations: List[str] = field(default_factory=lambda: ["infer", "compute", "train"])
    allowed_export_formats: List[str] = field(default_factory=lambda: ["encrypted_checkpoint"])

    @staticmethod
    def hipaa_compliant() -> "SovereignPolicy":
        return SovereignPolicy(
            residency=DataResidency.UNITED_STATES,
            classification=DataClassification.SECRET,
            encrypt_at_rest=True, encrypt_in_transit=True,
            encryption_standard=EncryptionStandard.AES_256_GCM,
            key_management=KeyManagement.CUSTOMER_MANAGED,
            attestation=True, audit=True,
            data_never_crosses_border=True,
            max_data_retention_days=2555,  # 7 years per HIPAA
        )

    @staticmethod
    def gdpr_compliant() -> "SovereignPolicy":
        return SovereignPolicy(
            residency=DataResidency.EUROPEAN_UNION,
            classification=DataClassification.CONFIDENTIAL,
            encrypt_at_rest=True, encrypt_in_transit=True,
            attestation=True, audit=True,
            data_never_crosses_border=True,
            max_data_retention_days=365,
        )

    @staticmethod
    def uae_sovereign() -> "SovereignPolicy":
        return SovereignPolicy(
            residency=DataResidency.UAE,
            classification=DataClassification.SOVEREIGN_SECRET,
            encrypt_at_rest=True, encrypt_in_transit=True,
            encryption_standard=EncryptionStandard.AES_256_GCM,
            key_management=KeyManagement.HARDWARE_GENERATED,
            attestation=True, audit=True,
            data_never_crosses_border=True,
            max_data_retention_days=3650,
        )

@dataclass
class AttestationReport:
    """Hardware attestation report."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = "prometheus-001"
    chip_type: str = "Prometheus"
    firmware_hash: str = field(default_factory=lambda: hashlib.sha256(b"firmware_v2.1").hexdigest())
    boot_measurements: List[str] = field(default_factory=lambda: [
        hashlib.sha256(b"stage0_bootrom").hexdigest()[:16],
        hashlib.sha256(b"stage1_fsbl").hexdigest()[:16],
        hashlib.sha256(b"stage2_runtime").hexdigest()[:16],
    ])
    timestamp: float = field(default_factory=time.time)
    signature: str = field(default_factory=lambda: hashlib.sha384(b"attestation_sig").hexdigest())
    valid: bool = True
    tpm_pcr_values: Dict[str, str] = field(default_factory=lambda: {
        "PCR0": hashlib.sha256(b"pcr0").hexdigest()[:16],
        "PCR1": hashlib.sha256(b"pcr1").hexdigest()[:16],
        "PCR7": hashlib.sha256(b"pcr7").hexdigest()[:16],
    })

    def verify(self) -> bool:
        return self.valid

    def to_json(self) -> str:
        return json.dumps({
            "report_id": self.report_id,
            "device_id": self.device_id,
            "firmware_hash": self.firmware_hash,
            "boot_measurements": self.boot_measurements,
            "valid": self.valid,
            "tpm_pcr_values": self.tpm_pcr_values,
        }, indent=2)

class AuditLog:
    """Tamper-proof audit log with hash chain."""
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
        self._prev_hash = "0" * 64

    def record(self, operation: str, details: Dict[str, Any] = None):
        entry = {
            "seq": len(self.entries),
            "operation": operation,
            "timestamp": time.time(),
            "details": details or {},
            "prev_hash": self._prev_hash,
        }
        entry_bytes = json.dumps(entry, sort_keys=True).encode()
        entry["hash"] = hashlib.sha256(entry_bytes).hexdigest()
        self._prev_hash = entry["hash"]
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for entry in self.entries:
            if entry["prev_hash"] != prev:
                return False
            check = dict(entry)
            stored_hash = check.pop("hash")
            computed = hashlib.sha256(json.dumps(check, sort_keys=True).encode()).hexdigest()
            if computed != stored_hash:
                return False
            prev = stored_hash
        return True

    def export_for_auditor(self, format: str = "json") -> str:
        return json.dumps({
            "format": format,
            "entries": len(self.entries),
            "chain_valid": self.verify_chain(),
            "log": self.entries,
        }, indent=2)

    def __len__(self):
        return len(self.entries)

class SovereignContext:
    """Simulated SovereignContext matching the real API."""
    _stack: List["SovereignContext"] = []

    def __init__(self, country: str = "ae", encrypt: bool = True,
                 audit: bool = True, attestation: bool = True,
                 policy: SovereignPolicy = None,
                 classification: str = "CONFIDENTIAL"):
        self.country = country
        self.encrypt = encrypt
        self.audit_enabled = audit
        self.attestation_enabled = attestation
        self.policy = policy or SovereignPolicy(residency=DataResidency(country))
        self.classification = classification
        self.audit_log = AuditLog()
        self._attestation_report: Optional[AttestationReport] = None

    def __enter__(self):
        SovereignContext._stack.append(self)
        self.audit_log.record("context_entered", {"country": self.country})
        if self.attestation_enabled:
            self._attestation_report = AttestationReport()
        return self

    def __exit__(self, *args):
        self.audit_log.record("context_exited", {"country": self.country})
        if SovereignContext._stack:
            SovereignContext._stack.pop()

    @staticmethod
    def get_active() -> Optional["SovereignContext"]:
        return SovereignContext._stack[-1] if SovereignContext._stack else None

    def get_attestation(self) -> AttestationReport:
        if self._attestation_report is None:
            self._attestation_report = AttestationReport()
        return self._attestation_report

# ── Simulated compute / infer ───────────────────────────────────────────

def _sim_compute(expr, inputs=None, **kw):
    ctx = SovereignContext.get_active()
    if ctx:
        ctx.audit_log.record("compute", {"expression": expr})
    time.sleep(0.01)
    return type("Result", (), {"output": {"result": "computed"}, "latency_ms": 1.2})()

def _sim_infer(model, prompt="", **kw):
    ctx = SovereignContext.get_active()
    if ctx:
        ctx.audit_log.record("inference", {"model": model})
    time.sleep(0.02)
    return type("Result", (), {"output": {"text": f"AI response to: {prompt[:40]}"},
                                "latency_ms": 35.0})()

class _SimZh:
    __version__ = "0.2.0"
    SovereignContext = SovereignContext
    SovereignPolicy = SovereignPolicy
    DataResidency = DataResidency
    DataClassification = DataClassification
    AttestationReport = AttestationReport
    AuditLog = AuditLog
    compute = staticmethod(_sim_compute)
    infer = staticmethod(_sim_infer)

try:
    import zhilicon as zh
except ImportError:
    zh = _SimZh()

# =============================================================================
# TUTORIAL
# =============================================================================

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def tutorial_sovereign_context():
    """SovereignContext: basic, nested, composable."""
    section("1. SovereignContext -- Basic, Nested, Composable")

    # --- Basic ---
    print("--- Basic SovereignContext ---")
    with zh.SovereignContext(country="ae", encrypt=True, audit=True) as ctx:
        result = zh.infer("zhilicon/arabic-llm-70b", prompt="Hello from UAE")
        print(f"Country: {ctx.country}, Encrypted: {ctx.encrypt}")
        print(f"Result: {result.output['text']}")

    # --- Nested (inner overrides outer) ---
    print("\n--- Nested Contexts ---")
    with zh.SovereignContext(country="ae", encrypt=True) as outer:
        print(f"Outer: country={outer.country}")
        zh.compute("A = 1 + 1")

        with zh.SovereignContext(country="sa", encrypt=True) as inner:
            print(f"Inner: country={inner.country}")
            zh.compute("B = 2 + 2")  # This follows Saudi sovereignty

            active = zh.SovereignContext.get_active()
            print(f"Active context: country={active.country}")

        # Back to outer context
        active = zh.SovereignContext.get_active()
        print(f"After inner exits: country={active.country}")

    # --- Composable (reuse policies) ---
    print("\n--- Composable with Reusable Policies ---")
    hipaa_policy = SovereignPolicy.hipaa_compliant()
    gdpr_policy = SovereignPolicy.gdpr_compliant()

    with zh.SovereignContext(country="us", policy=hipaa_policy) as ctx:
        print(f"HIPAA context: residency={ctx.policy.residency.value}, "
              f"retention={ctx.policy.max_data_retention_days} days")

    with zh.SovereignContext(country="eu", policy=gdpr_policy) as ctx:
        print(f"GDPR context: residency={ctx.policy.residency.value}, "
              f"retention={ctx.policy.max_data_retention_days} days")


def tutorial_sovereign_policy():
    """SovereignPolicy: presets and custom configuration."""
    section("2. SovereignPolicy -- Presets and Custom")

    # --- Preset policies ---
    print("--- Preset Policies ---")
    presets = {
        "HIPAA": SovereignPolicy.hipaa_compliant(),
        "GDPR": SovereignPolicy.gdpr_compliant(),
        "UAE Sovereign": SovereignPolicy.uae_sovereign(),
    }

    for name, policy in presets.items():
        print(f"\n  {name}:")
        print(f"    Residency      : {policy.residency.value}")
        print(f"    Classification : {policy.classification.value}")
        print(f"    Encryption     : {policy.encryption_standard.value}")
        print(f"    Key management : {policy.key_management.value}")
        print(f"    Cross-border   : {'blocked' if policy.data_never_crosses_border else 'allowed'}")
        print(f"    Retention      : {policy.max_data_retention_days} days")

    # --- Custom policy ---
    print("\n--- Custom Policy ---")
    custom = SovereignPolicy(
        residency=DataResidency.SINGAPORE,
        classification=DataClassification.SECRET,
        encrypt_at_rest=True,
        encrypt_in_transit=True,
        encryption_standard=EncryptionStandard.AES_256_GCM,
        key_management=KeyManagement.CUSTOMER_MANAGED,
        attestation=True,
        audit=True,
        data_never_crosses_border=True,
        max_data_retention_days=180,
        allowed_operations=["infer"],  # Read-only: no training allowed
    )
    print(f"  Singapore custom policy:")
    print(f"    Allowed ops: {custom.allowed_operations}")
    print(f"    Retention  : {custom.max_data_retention_days} days")


def tutorial_attestation():
    """Attestation: hardware integrity proofs."""
    section("3. Attestation -- Hardware Integrity Proofs")

    print("Attestation proves the hardware hasn't been tampered with.")
    print("It uses TPM (Trusted Platform Module) measurements.\n")

    with zh.SovereignContext(country="ae", attestation=True) as ctx:
        # Request attestation report
        report = ctx.get_attestation()

        print(f"Report ID       : {report.report_id}")
        print(f"Device          : {report.device_id}")
        print(f"Chip            : {report.chip_type}")
        print(f"Firmware hash   : {report.firmware_hash[:32]}...")

        print(f"\nBoot measurements (secure boot chain):")
        stages = ["Stage 0 (BootROM)", "Stage 1 (FSBL)", "Stage 2 (Runtime)"]
        for stage, measurement in zip(stages, report.boot_measurements):
            print(f"  {stage}: {measurement}")

        print(f"\nTPM PCR values:")
        for pcr, value in report.tpm_pcr_values.items():
            print(f"  {pcr}: {value}")

        # Verify the attestation
        is_valid = report.verify()
        print(f"\nAttestation valid: {is_valid}")

        # Export for external verification
        report_json = report.to_json()
        print(f"\nExported report ({len(report_json)} bytes JSON)")


def tutorial_audit_log():
    """AuditLog: tamper-proof operation recording."""
    section("4. AuditLog -- Tamper-Proof Operation Recording")

    with zh.SovereignContext(country="ae", audit=True) as ctx:
        # Run some operations
        zh.compute("A = 1 + 1")
        zh.infer("zhilicon/llama-7b-fp8", prompt="Test query")
        zh.compute("B = 2 * 3")

        # Inspect the audit log
        print(f"Audit log has {len(ctx.audit_log)} entries:\n")
        for entry in ctx.audit_log.entries:
            print(f"  [{entry['seq']:3d}] {entry['operation']:20s} "
                  f"hash={entry['hash'][:12]}... "
                  f"prev={entry['prev_hash'][:12]}...")

        # Verify the hash chain (tamper detection)
        chain_valid = ctx.audit_log.verify_chain()
        print(f"\nHash chain integrity: {'VALID' if chain_valid else 'TAMPERED!'}")

        # Export for auditors (HIPAA, GDPR compliance)
        export = ctx.audit_log.export_for_auditor(format="json")
        export_data = json.loads(export)
        print(f"\nExported for auditor:")
        print(f"  Entries: {export_data['entries']}")
        print(f"  Chain valid: {export_data['chain_valid']}")
        print(f"  Export size: {len(export)} bytes")


def tutorial_data_residency():
    """DataResidency: all supported regions."""
    section("5. DataResidency -- All Supported Regions")

    print("Zhilicon supports data residency in these regions:\n")
    regions = {
        DataResidency.UAE: ("United Arab Emirates", "Abu Dhabi, Dubai"),
        DataResidency.SAUDI_ARABIA: ("Saudi Arabia", "Riyadh, Jeddah"),
        DataResidency.UNITED_STATES: ("United States", "Virginia, Oregon, Texas"),
        DataResidency.EUROPEAN_UNION: ("European Union", "Frankfurt, Dublin, Amsterdam"),
        DataResidency.INDIA: ("India", "Mumbai, Chennai"),
        DataResidency.SINGAPORE: ("Singapore", "Singapore"),
        DataResidency.JAPAN: ("Japan", "Tokyo, Osaka"),
        DataResidency.SOUTH_KOREA: ("South Korea", "Seoul"),
        DataResidency.UNITED_KINGDOM: ("United Kingdom", "London"),
        DataResidency.GERMANY: ("Germany", "Frankfurt"),
        DataResidency.FRANCE: ("France", "Paris"),
        DataResidency.BRAZIL: ("Brazil", "Sao Paulo"),
        DataResidency.CANADA: ("Canada", "Montreal, Toronto"),
        DataResidency.AUSTRALIA: ("Australia", "Sydney"),
    }

    for residency, (name, locations) in regions.items():
        print(f"  {residency.value:4s} | {name:25s} | {locations}")

    # Use residency in a context
    print(f"\nExample: Data pinned to Saudi Arabia")
    policy = SovereignPolicy(
        residency=DataResidency.SAUDI_ARABIA,
        data_never_crosses_border=True,
    )
    with zh.SovereignContext(country="sa", policy=policy) as ctx:
        print(f"  Residency: {ctx.policy.residency.value}")
        print(f"  Cross-border: {'blocked' if ctx.policy.data_never_crosses_border else 'allowed'}")


def tutorial_data_classification():
    """DataClassification: security levels."""
    section("6. DataClassification -- Security Levels")

    print("Zhilicon supports 6 classification levels:\n")
    classifications = [
        (DataClassification.PUBLIC, "No restrictions, can be shared freely"),
        (DataClassification.INTERNAL, "Internal use only, not for public"),
        (DataClassification.CONFIDENTIAL, "Encrypted, access-controlled"),
        (DataClassification.SECRET, "Encrypted, audited, attested"),
        (DataClassification.TOP_SECRET, "Hardware-isolated, no export"),
        (DataClassification.SOVEREIGN_SECRET, "Nation-level, hardware key destruction on expiry"),
    ]

    for cls, desc in classifications:
        print(f"  {cls.value:20s} | {desc}")

    # Each classification level implies different encryption and access controls
    print(f"\nClassification determines automatic security controls:")
    print(f"  PUBLIC       -> No encryption, no audit")
    print(f"  INTERNAL     -> TLS in transit")
    print(f"  CONFIDENTIAL -> AES-256-GCM + audit")
    print(f"  SECRET       -> AES-256-GCM + audit + attestation")
    print(f"  TOP_SECRET   -> AES-256-GCM + audit + attestation + HW isolation")
    print(f"  SOVEREIGN    -> All above + HW key destruction on expiry")


def main():
    print("=" * 60)
    print("  Zhilicon Tutorial 02: Sovereign Computing Deep Dive")
    print("=" * 60)

    tutorial_sovereign_context()
    tutorial_sovereign_policy()
    tutorial_attestation()
    tutorial_audit_log()
    tutorial_data_residency()
    tutorial_data_classification()

    print(f"\nTutorial complete! Next: 03_medical_imaging.py")


if __name__ == "__main__":
    main()

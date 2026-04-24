#!/usr/bin/env python3
"""
Zhilicon Tutorial 09 -- Compliance Automation
===============================================

Compliance automation tutorial:
  1. Enable regulations (GDPR, HIPAA, PDPL)
  2. Run compliance checks
  3. Handle violations
  4. Generate compliance reports
  5. Export for auditors

How to run:
    pip install zhilicon
    python 09_compliance.py

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys, time, random, hashlib, json, uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# ── Simulation layer ────────────────────────────────────────────────────

class Regulation(Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PDPL_SAUDI = "pdpl_sa"
    UAE_DATA_LAW = "uae_data"
    FIPS_140_3 = "fips_140_3"
    SOC_2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"

class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"

@dataclass
class ComplianceCheck:
    regulation: str
    rule_id: str
    description: str
    passed: bool
    severity: str
    details: str = ""
    remediation: str = ""

@dataclass
class ComplianceReport:
    regulations: List[str]
    checks_performed: int
    checks_passed: int
    checks_failed: int
    violations: List[ComplianceCheck]
    warnings: List[ComplianceCheck]
    timestamp: float = field(default_factory=time.time)
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def is_compliant(self):
        return len(self.violations) == 0

    def to_json(self):
        return json.dumps({
            "compliant": self.is_compliant,
            "regulations": self.regulations,
            "summary": {"total": self.checks_performed, "passed": self.checks_passed,
                        "failed": self.checks_failed},
            "violations": [{"rule": v.rule_id, "desc": v.description,
                           "fix": v.remediation} for v in self.violations],
        }, indent=2)

class ComplianceEngine:
    def __init__(self):
        self._enabled: List[Regulation] = []
        self._last_report: Optional[ComplianceReport] = None
        self._metadata: Dict = {}

    def enable(self, regulation: Regulation):
        self._enabled.append(regulation)
        print(f"  Enabled: {regulation.value}")

    def set_metadata(self, **kwargs):
        self._metadata.update(kwargs)

    def check(self, context: Dict = None) -> ComplianceReport:
        ctx = context or self._metadata
        checks = []
        violations = []
        warnings = []
        for reg in self._enabled:
            reg_checks = self._run_checks(reg, ctx)
            checks.extend(reg_checks)
            for c in reg_checks:
                if not c.passed:
                    if c.severity in ("violation", "critical"):
                        violations.append(c)
                    else:
                        warnings.append(c)
        report = ComplianceReport(
            regulations=[r.value for r in self._enabled],
            checks_performed=len(checks), checks_passed=sum(1 for c in checks if c.passed),
            checks_failed=sum(1 for c in checks if not c.passed),
            violations=violations, warnings=warnings)
        self._last_report = report
        return report

    def _run_checks(self, reg: Regulation, ctx: Dict) -> List[ComplianceCheck]:
        checks = []
        if reg == Regulation.GDPR:
            checks.append(ComplianceCheck(reg.value, "Art5.1.b", "Purpose limitation",
                          bool(ctx.get("purpose")), "violation",
                          remediation="Declare processing purpose"))
            checks.append(ComplianceCheck(reg.value, "Art5.1.f", "Integrity and confidentiality",
                          ctx.get("encrypted", False), "violation",
                          remediation="Enable encryption"))
            checks.append(ComplianceCheck(reg.value, "Art30", "Records of processing",
                          ctx.get("audit", False), "violation",
                          remediation="Enable audit logging"))
            checks.append(ComplianceCheck(reg.value, "Art44", "International transfers",
                          ctx.get("no_cross_border", False), "violation",
                          remediation="Block cross-border transfers"))
        elif reg == Regulation.HIPAA:
            checks.append(ComplianceCheck(reg.value, "164.312.a.2.iv", "Encryption at rest",
                          ctx.get("encrypted", False), "violation",
                          remediation="Enable encryption at rest"))
            checks.append(ComplianceCheck(reg.value, "164.312.b", "Audit controls",
                          ctx.get("audit", False), "violation",
                          remediation="Enable audit logging"))
            checks.append(ComplianceCheck(reg.value, "164.312.a.1", "Access control",
                          bool(ctx.get("user_id")), "violation",
                          remediation="Provide user identification"))
        elif reg == Regulation.PDPL_SAUDI:
            checks.append(ComplianceCheck(reg.value, "Art29", "Data residency",
                          ctx.get("country") == "sa", "violation",
                          remediation="Set residency to Saudi Arabia"))
            checks.append(ComplianceCheck(reg.value, "Art5", "Consent basis",
                          bool(ctx.get("purpose")), "violation",
                          remediation="Declare processing purpose"))
        return checks

    def enforce(self, **metadata):
        return _ComplianceContext(self, metadata)

    def last_report(self): return self._last_report

class _ComplianceContext:
    def __init__(self, engine, metadata):
        self._engine = engine
        self._metadata = metadata
    def __enter__(self):
        self._engine.set_metadata(**self._metadata)
        report = self._engine.check(self._metadata)
        if not report.is_compliant:
            print(f"\n  WARNING: {len(report.violations)} compliance violation(s) detected!")
            for v in report.violations:
                print(f"    [{v.regulation}:{v.rule_id}] {v.description}")
                print(f"      Fix: {v.remediation}")
        return self
    def __exit__(self, *a): pass

# ── Tutorial ────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}\n")

def tutorial_enable_regulations():
    section("1. Enable Regulations")
    engine = ComplianceEngine()
    print("Enabling compliance regulations:\n")
    engine.enable(Regulation.GDPR)
    engine.enable(Regulation.HIPAA)
    engine.enable(Regulation.PDPL_SAUDI)
    print(f"\n{len(engine._enabled)} regulations active.")
    print(f"All operations will be checked against these regulations.")
    return engine

def tutorial_run_checks(engine):
    section("2. Run Compliance Checks")
    # Check with a COMPLIANT context
    print("--- Compliant context ---")
    report = engine.check({
        "purpose": "medical_diagnosis", "encrypted": True, "audit": True,
        "no_cross_border": True, "user_id": "DR-001", "country": "sa",
    })
    print(f"  Checks: {report.checks_passed}/{report.checks_performed} passed")
    print(f"  Compliant: {report.is_compliant}")
    # Check with a NON-COMPLIANT context
    print(f"\n--- Non-compliant context (missing purpose, no encryption) ---")
    report2 = engine.check({"country": "us"})  # Missing many fields
    print(f"  Checks: {report2.checks_passed}/{report2.checks_performed} passed")
    print(f"  Violations: {len(report2.violations)}")
    for v in report2.violations:
        print(f"    [{v.regulation}:{v.rule_id}] {v.description}")
    return report2

def tutorial_handle_violations(report):
    section("3. Handle Violations")
    if not report.is_compliant:
        print(f"Found {len(report.violations)} violation(s). Remediation steps:\n")
        for i, v in enumerate(report.violations, 1):
            print(f"  {i}. [{v.regulation}:{v.rule_id}] {v.description}")
            print(f"     Remediation: {v.remediation}")
        print(f"\nAfter applying fixes, re-run compliance check to verify.")

def tutorial_generate_reports(engine):
    section("4. Generate Compliance Reports")
    report = engine.check({
        "purpose": "patient_monitoring", "encrypted": True, "audit": True,
        "no_cross_border": True, "user_id": "DR-042", "country": "sa",
    })
    print(f"Compliance Report (Session: {report.session_id}):")
    print(f"  Regulations  : {', '.join(report.regulations)}")
    print(f"  Total checks : {report.checks_performed}")
    print(f"  Passed       : {report.checks_passed}")
    print(f"  Failed       : {report.checks_failed}")
    print(f"  Violations   : {len(report.violations)}")
    print(f"  Warnings     : {len(report.warnings)}")
    print(f"  COMPLIANT    : {report.is_compliant}")
    return report

def tutorial_export_for_auditors(report):
    section("5. Export for Auditors")
    export_json = report.to_json()
    print(f"Exported compliance report ({len(export_json)} bytes JSON):\n")
    parsed = json.loads(export_json)
    print(json.dumps(parsed, indent=2)[:500])
    print(f"\nThis report can be submitted to:")
    print(f"  - HIPAA auditors (HHS OCR)")
    print(f"  - GDPR supervisory authorities (DPAs)")
    print(f"  - Saudi NDMO (PDPL enforcement)")
    print(f"  - Internal compliance teams")
    print(f"\nReports are machine-verifiable, not Word documents.")

def main():
    print("=" * 60)
    print("  Zhilicon Tutorial 09: Compliance Automation")
    print("=" * 60)
    engine = tutorial_enable_regulations()
    report = tutorial_run_checks(engine)
    tutorial_handle_violations(report)
    compliant_report = tutorial_generate_reports(engine)
    tutorial_export_for_auditors(compliant_report)
    print(f"\nTutorial complete! Next: 10_advanced_sovereignty.py")

if __name__ == "__main__":
    main()

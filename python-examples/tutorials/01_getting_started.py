#!/usr/bin/env python3
"""
Zhilicon Tutorial 01 -- Getting Started
=========================================

A complete getting-started guide for the Zhilicon platform.
Every line is commented. Every concept is explained.

Topics covered:
  1. Device discovery -- find all Zhilicon hardware
  2. Tensor creation -- create and manipulate tensors
  3. Simple computation -- run declarative compute
  4. Sovereignty basics -- your first SovereignContext
  5. Error handling -- what can go wrong and how to fix it
  6. Configuration -- customize Zhilicon behavior

How to run:
    pip install zhilicon
    python 01_getting_started.py

Prerequisites: None. Works in simulation mode without hardware.

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

# =============================================================================
# PREAMBLE: Simulation Layer
# =============================================================================
# This simulation layer lets the tutorial run WITHOUT real Zhilicon hardware.
# In production, you just `pip install zhilicon` and all of this is real.

import sys
import time
import random
import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

# ── Simulated SDK types ─────────────────────────────────────────────────

class _ChipType:
    Discovery1 = 0x01
    Horizon1 = 0x02
    Nexus1 = 0x03
    Sentinel1 = 0x04
    Prometheus = 0x05
    Simulated = 0xFF

@dataclass
class _DeviceInfo:
    device_id: int
    chip: int
    name: str
    global_mem_size: int
    compute_units: int
    max_clock_mhz: int
    hbm_bandwidth_gbps: int
    tflops_fp16: float
    tops_int8: float

class _Device:
    def __init__(self, info: _DeviceInfo):
        self._info = info
        self._valid = True

    @staticmethod
    def enumerate() -> List[_DeviceInfo]:
        return [
            _DeviceInfo(0, _ChipType.Prometheus, "Prometheus (simulated)",
                        96 * 1024**3, 512, 2100, 4800, 500.0, 1000.0),
            _DeviceInfo(1, _ChipType.Discovery1, "Discovery-1 (simulated)",
                        32 * 1024**3, 128, 1800, 1200, 125.0, 250.0),
            _DeviceInfo(2, _ChipType.Sentinel1, "Sentinel-1 (simulated)",
                        16 * 1024**3, 64, 1500, 600, 62.5, 125.0),
        ]

    @staticmethod
    def open(device_id: int) -> "_Device":
        devices = _Device.enumerate()
        for d in devices:
            if d.device_id == device_id:
                return _Device(d)
        raise RuntimeError(f"Device {device_id} not found")

    @staticmethod
    def open_simulated(chip=None) -> "_Device":
        return _Device(_DeviceInfo(
            9999, _ChipType.Simulated, "Simulated Device",
            256 * 1024**2, 64, 1500, 900, 125.0, 250.0,
        ))

    @property
    def info(self): return self._info
    @property
    def is_valid(self): return self._valid
    def temperature(self): return random.uniform(55, 75)
    def power(self): return random.uniform(150, 250)
    def close(self): self._valid = False
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

class _DType:
    float32 = "float32"
    float16 = "float16"
    bfloat16 = "bfloat16"
    int8 = "int8"
    fp8_e4m3 = "fp8_e4m3"

class _Tensor:
    def __init__(self, shape, dtype="float32", data=None):
        self.shape = shape
        self.dtype = dtype
        size = 1
        for s in shape:
            size *= s
        self.data = data if data is not None else [random.gauss(0, 1) for _ in range(min(size, 100))]
        self._size = size

    @staticmethod
    def zeros(shape, dtype="float32"):
        return _Tensor(shape, dtype, data=[0.0] * min(math.prod(shape), 100))

    @staticmethod
    def ones(shape, dtype="float32"):
        return _Tensor(shape, dtype, data=[1.0] * min(math.prod(shape), 100))

    @staticmethod
    def randn(shape, dtype="float32"):
        return _Tensor(shape, dtype)

    def __repr__(self):
        return f"Tensor(shape={self.shape}, dtype={self.dtype})"

    def __matmul__(self, other):
        if len(self.shape) != 2 or len(other.shape) != 2:
            raise ValueError("matmul requires 2D tensors")
        if self.shape[1] != other.shape[0]:
            raise ValueError(f"Shape mismatch: {self.shape} @ {other.shape}")
        return _Tensor((self.shape[0], other.shape[1]), self.dtype)

    def sum(self):
        return sum(self.data[:min(len(self.data), 10)])

    def mean(self):
        n = min(len(self.data), 10)
        return sum(self.data[:n]) / n if n > 0 else 0.0

    def to(self, dtype):
        return _Tensor(self.shape, dtype, self.data)

class _ComputeResult:
    def __init__(self, output, latency_ms=1.0, device="Simulated"):
        self.output = output
        self.latency_ms = latency_ms
        self.device = device

class _AuditEntry:
    def __init__(self, op, ts, details, h):
        self.operation = op
        self.timestamp = ts
        self.details = details
        self.hash = h

class _AuditLog:
    def __init__(self):
        self.entries: List[_AuditEntry] = []
    def record(self, op, details=None):
        self.entries.append(_AuditEntry(op, time.time(), details or {},
                                        hashlib.sha256(f"{op}{time.time()}".encode()).hexdigest()[:16]))
    def __len__(self): return len(self.entries)

class _SovereignContext:
    _stack: List["_SovereignContext"] = []
    def __init__(self, country="ae", encrypt=True, audit=True, attestation=True,
                 classification="CONFIDENTIAL"):
        self.country = country
        self.encrypt = encrypt
        self.audit_enabled = audit
        self.attestation = attestation
        self.classification = classification
        self.audit_log = _AuditLog()
    def __enter__(self):
        _SovereignContext._stack.append(self)
        self.audit_log.record("context_opened")
        return self
    def __exit__(self, *a):
        self.audit_log.record("context_closed")
        if _SovereignContext._stack:
            _SovereignContext._stack.pop()
    @staticmethod
    def get_active():
        return _SovereignContext._stack[-1] if _SovereignContext._stack else None

def _compute(expression, inputs=None, constraints=None):
    time.sleep(0.01)
    if "A @ B" in expression and inputs:
        A = inputs.get("A")
        B = inputs.get("B")
        if A and B:
            C = A.__matmul__(B)
            return _ComputeResult({"C": C}, latency_ms=random.uniform(0.5, 2.0))
    return _ComputeResult({"result": _Tensor((1,))}, latency_ms=random.uniform(0.5, 2.0))

def _infer(model, prompt="", **kwargs):
    time.sleep(0.03)
    return _ComputeResult(
        {"text": f"Response to: {prompt[:50]}...", "tokens": 42},
        latency_ms=random.uniform(30, 60),
    )

class _Constraint:
    def __init__(self, latency_ms=None, power_watts=None, memory_mb=None):
        self.latency_ms = latency_ms
        self.power_watts = power_watts
        self.memory_mb = memory_mb

# Assemble a simulated "zh" module
class _SimZh:
    __version__ = "0.2.0"
    Device = _Device
    ChipType = _ChipType
    DeviceInfo = _DeviceInfo
    Tensor = _Tensor
    DType = _DType
    SovereignContext = _SovereignContext
    Constraint = _Constraint
    compute = staticmethod(_compute)
    infer = staticmethod(_infer)

try:
    import zhilicon as zh
except ImportError:
    zh = _SimZh()

# =============================================================================
# TUTORIAL BEGINS HERE
# =============================================================================

def section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: DEVICE DISCOVERY
# ─────────────────────────────────────────────────────────────────────────────

def tutorial_device_discovery():
    """
    Discover all Zhilicon devices available on this system.

    Zhilicon supports 5 chip architectures:
      - Prometheus    : Flagship training/inference chip (500 TFLOPS FP16)
      - Discovery-1   : Medical AI processor
      - Horizon-1     : Space-grade AI (radiation-hardened)
      - Sentinel-1    : Cryptographic accelerator
      - Nexus-1       : 6G telecom processor
    """
    section("1. DEVICE DISCOVERY")

    # Enumerate all available devices
    # This works like nvidia-smi but for Zhilicon hardware
    devices = zh.Device.enumerate()
    print(f"Found {len(devices)} Zhilicon device(s):\n")

    for dev in devices:
        mem_gb = dev.global_mem_size / (1024**3)
        print(f"  [{dev.device_id}] {dev.name}")
        print(f"      Memory      : {mem_gb:.0f} GB HBM")
        print(f"      Compute     : {dev.compute_units} CUs @ {dev.max_clock_mhz} MHz")
        print(f"      FP16 TFLOPS : {dev.tflops_fp16}")
        print(f"      INT8 TOPS   : {dev.tops_int8}")
        print(f"      HBM BW      : {dev.hbm_bandwidth_gbps} GB/s")
        print()

    # Open a specific device
    # The Device object is a context manager -- it auto-closes when done
    with zh.Device.open(devices[0].device_id) as dev:
        print(f"Opened device: {dev.info.name}")
        print(f"  Temperature : {dev.temperature():.1f} C")
        print(f"  Power       : {dev.power():.1f} W")

    # You can also open a simulated device (for development without hardware)
    sim_dev = zh.Device.open_simulated()
    print(f"\nSimulated device: {sim_dev.info.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: TENSOR CREATION
# ─────────────────────────────────────────────────────────────────────────────

def tutorial_tensor_creation():
    """
    Create and manipulate tensors on Zhilicon hardware.

    Zhilicon tensors are similar to NumPy/PyTorch tensors but with:
      - Automatic encryption (when inside a SovereignContext)
      - Hardware-specific optimizations (FP8, INT8 auto-quantization)
      - Zero-copy device transfers
    """
    section("2. TENSOR CREATION")

    # Create tensors -- same API you already know
    zeros = zh.Tensor.zeros((3, 4))
    ones = zh.Tensor.ones((3, 4))
    randn = zh.Tensor.randn((3, 4))
    print(f"Zeros  : {zeros}")
    print(f"Ones   : {ones}")
    print(f"Random : {randn}")

    # Supported data types -- including Zhilicon-exclusive FP8
    print(f"\nSupported dtypes:")
    for dtype in [zh.DType.float32, zh.DType.float16, zh.DType.bfloat16,
                  zh.DType.int8, zh.DType.fp8_e4m3]:
        t = zh.Tensor.randn((2, 2), dtype=dtype)
        print(f"  {dtype:12s} -> {t}")

    # Matrix multiplication
    A = zh.Tensor.randn((128, 256))
    B = zh.Tensor.randn((256, 64))
    C = A @ B  # Zhilicon's systolic array handles this
    print(f"\nMatrix multiply: {A} @ {B} = {C}")

    # Cast to different precision
    A_fp16 = A.to(zh.DType.float16)
    print(f"Cast to FP16: {A_fp16}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: SIMPLE COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

def tutorial_simple_computation():
    """
    Run declarative computation on Zhilicon.

    Zhilicon's compute API is DECLARATIVE: you describe WHAT to compute,
    not HOW. The compiler decides the optimal execution strategy.

    Compare to CUDA:
      CUDA:     Launch kernel, manage memory, synchronize, copy back
      Zhilicon: compute("C = A @ B", inputs={"A": a, "B": b})
    """
    section("3. SIMPLE COMPUTATION (Declarative)")

    # Create input tensors
    A = zh.Tensor.randn((64, 128))
    B = zh.Tensor.randn((128, 32))

    # Declarative compute -- ONE LINE replaces pages of CUDA code
    # The Zhilicon compiler:
    #   1. Parses the expression
    #   2. Selects the optimal kernel
    #   3. Manages memory allocation
    #   4. Handles data placement
    #   5. Returns the result
    result = zh.compute(
        "C = A @ B",
        inputs={"A": A, "B": B},
    )
    print(f"Compute result: C = {result.output['C']}")
    print(f"Latency: {result.latency_ms:.2f} ms")

    # With constraints -- tell the compiler what matters to you
    result2 = zh.compute(
        "C = A @ B",
        inputs={"A": A, "B": B},
        constraints=zh.Constraint(latency_ms=5.0),  # Must finish in 5ms
    )
    print(f"\nWith latency constraint (5ms): {result2.latency_ms:.2f} ms")

    # Run inference -- even simpler
    result3 = zh.infer(
        "zhilicon/llama-7b-fp8",
        prompt="What is machine learning?",
        max_tokens=100,
    )
    print(f"\nInference result: {result3.output['text'][:100]}...")


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: SOVEREIGNTY BASICS
# ─────────────────────────────────────────────────────────────────────────────

def tutorial_sovereignty_basics():
    """
    Introduction to Zhilicon's killer feature: Data Sovereignty.

    SovereignContext wraps your computation with guarantees:
      - Data stays in the country you specify
      - Data is encrypted at rest and in transit
      - Every operation is logged (tamper-proof audit trail)
      - Hardware attests that it hasn't been compromised

    No other chip platform has this. NVIDIA? Zero sovereignty. AMD? Zero.
    """
    section("4. SOVEREIGNTY BASICS")

    # Basic sovereignty -- wrap your code in a SovereignContext
    print("--- Basic SovereignContext ---")
    with zh.SovereignContext(country="ae", encrypt=True) as ctx:
        # Everything inside this block has UAE data sovereignty
        result = zh.infer("zhilicon/arabic-llm-70b",
                          prompt="Translate: Good morning")
        print(f"Country   : {ctx.country}")
        print(f"Encrypted : {ctx.encrypt}")
        print(f"Result    : {result.output['text'][:80]}...")

    # Sovereignty with audit logging
    print("\n--- With Audit Logging ---")
    with zh.SovereignContext(country="sa", encrypt=True, audit=True) as ctx:
        # Every operation is now logged
        result = zh.compute("C = A @ B",
                            inputs={"A": zh.Tensor.randn((4, 4)),
                                    "B": zh.Tensor.randn((4, 4))})
        print(f"Audit entries: {len(ctx.audit_log)}")
        for entry in ctx.audit_log.entries:
            print(f"  [{entry.hash[:8]}] {entry.operation}")

    # Nested sovereignty (inner context overrides outer)
    print("\n--- Nested Sovereignty ---")
    with zh.SovereignContext(country="ae", encrypt=True) as outer:
        print(f"Outer context: {outer.country}")
        with zh.SovereignContext(country="sa", encrypt=True) as inner:
            print(f"Inner context: {inner.country}")
            # Data here follows Saudi sovereignty
            active = zh.SovereignContext.get_active()
            if active:
                print(f"Active context: {active.country}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: ERROR HANDLING
# ─────────────────────────────────────────────────────────────────────────────

def tutorial_error_handling():
    """
    Zhilicon error handling best practices.

    Zhilicon raises clear, actionable exceptions:
      - RuntimeError: Hardware/driver issues
      - ValueError: Bad inputs (shape mismatch, invalid dtype)
      - ComplianceViolation: Regulation check failed
      - PermissionError: Sovereignty violation
    """
    section("5. ERROR HANDLING")

    # Shape mismatch (caught before execution)
    print("--- Shape Mismatch ---")
    try:
        A = zh.Tensor.randn((3, 4))
        B = zh.Tensor.randn((5, 6))  # Incompatible shapes
        C = A @ B  # This will raise ValueError
    except ValueError as e:
        print(f"Caught ValueError: {e}")
        print("Fix: Ensure inner dimensions match (A.shape[1] == B.shape[0])")

    # Device not found
    print("\n--- Device Not Found ---")
    try:
        dev = zh.Device.open(9999)  # Non-existent device
    except RuntimeError as e:
        print(f"Caught RuntimeError: {e}")
        print("Fix: Use Device.enumerate() to find available devices")

    # Correct shape -- this works
    print("\n--- Correct Usage ---")
    A = zh.Tensor.randn((3, 4))
    B = zh.Tensor.randn((4, 5))
    C = A @ B
    print(f"Success: {A} @ {B} = {C}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 6: PUTTING IT ALL TOGETHER
# ─────────────────────────────────────────────────────────────────────────────

def tutorial_putting_it_together():
    """
    A complete end-to-end example combining all concepts.
    """
    section("6. PUTTING IT ALL TOGETHER")

    # Step 1: Discover hardware
    devices = zh.Device.enumerate()
    print(f"Available devices: {len(devices)}")

    # Step 2: Create a sovereign computation context
    with zh.SovereignContext(
        country="ae",
        encrypt=True,
        audit=True,
        attestation=True,
        classification="CONFIDENTIAL",
    ) as ctx:
        # Step 3: Create tensors
        X = zh.Tensor.randn((32, 768))   # Input embeddings
        W = zh.Tensor.randn((768, 256))  # Weight matrix

        # Step 4: Run computation (declarative)
        result = zh.compute("Y = X @ W", inputs={"X": X, "W": W})
        Y = result.output.get("Y") or result.output.get("result")
        print(f"Input  : {X}")
        print(f"Weights: {W}")
        print(f"Output : {Y}")
        print(f"Latency: {result.latency_ms:.2f} ms")

        # Step 5: Run inference
        llm_result = zh.infer(
            "zhilicon/llama-7b-fp8",
            prompt="Summarize the benefits of sovereign AI computing.",
        )
        print(f"\nLLM: {llm_result.output['text'][:120]}...")

        # Step 6: Check audit trail
        print(f"\nAudit trail ({len(ctx.audit_log)} entries):")
        for entry in ctx.audit_log.entries:
            print(f"  {entry.operation:20s} | hash: {entry.hash[:12]}")

    print("\nTutorial complete! You now know the basics of Zhilicon.")
    print("Next: Try tutorial 02_sovereign_computing.py for advanced sovereignty.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all tutorial sections."""
    print("=" * 60)
    print("  Zhilicon Tutorial 01: Getting Started")
    print(f"  SDK Version: {zh.__version__}")
    print("=" * 60)

    tutorial_device_discovery()
    tutorial_tensor_creation()
    tutorial_simple_computation()
    tutorial_sovereignty_basics()
    tutorial_error_handling()
    tutorial_putting_it_together()


if __name__ == "__main__":
    main()

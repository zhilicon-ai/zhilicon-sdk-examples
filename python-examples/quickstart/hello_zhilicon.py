#!/usr/bin/env python3
"""
Zhilicon Quickstart -- Hello World
===================================

The SIMPLEST possible Zhilicon example. Five lines to your first inference.

This script demonstrates:
  1. Import the Zhilicon SDK
  2. Run a single inference call (one line!)
  3. Print the result

No configuration. No device management. No boilerplate.
Zhilicon handles device selection, model loading, and optimization automatically.

How to run:
    pip install zhilicon
    python hello_zhilicon.py

Expected output:
    Zhilicon SDK v0.2.0
    Running inference on zhilicon/llama-7b-fp8 ...
    --------------------------------------------------
    Prompt : Hello, world!
    Output : Hello, world! I am an AI assistant running on Zhilicon sovereign
             hardware. I can help you with a wide range of tasks ...
    --------------------------------------------------
    Latency     : 42.3 ms
    Tokens/sec  : 847
    Device      : Prometheus (simulated)
    Sovereignty : Default (no restrictions)

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

# ── Step 0: Simulate the Zhilicon SDK for standalone execution ──────────
# In production you just `pip install zhilicon` and skip this block.
# We include a self-contained simulation so the example runs anywhere.

import sys
import time
import random
import dataclasses
from typing import Any, Dict, Optional

class _SimulatedResult:
    """Simulated inference result matching the real zh.ComputeResult API."""
    def __init__(self, output: Dict[str, Any], latency_ms: float, device: str):
        self.output = output
        self.latency_ms = latency_ms
        self.device = device
        self.tokens_per_sec = int(len(output.get("text", "").split()) / (latency_ms / 1000)) if latency_ms > 0 else 0
        self.sovereign_context = "Default (no restrictions)"

class _SimulatedZhilicon:
    """Minimal Zhilicon SDK simulator for standalone demo."""
    __version__ = "0.2.0"

    def infer(self, model: str, prompt: str, max_tokens: int = 256,
              temperature: float = 0.7, **kwargs) -> _SimulatedResult:
        """Run inference on a Zhilicon-optimized model."""
        # Simulate realistic latency
        start = time.time()
        time.sleep(random.uniform(0.03, 0.06))  # ~40ms simulated
        latency = (time.time() - start) * 1000

        # Simulated response
        response_text = (
            f"{prompt} I am an AI assistant running on Zhilicon sovereign "
            f"hardware. I can help you with a wide range of tasks including "
            f"code generation, analysis, translation, and creative writing. "
            f"All computation happens with full data sovereignty -- your data "
            f"never leaves the jurisdiction you specify."
        )

        return _SimulatedResult(
            output={"text": response_text, "tokens_generated": 52, "finish_reason": "stop"},
            latency_ms=latency,
            device="Prometheus (simulated)",
        )

# Use the real SDK if available, otherwise use simulation
try:
    import zhilicon as zh
except ImportError:
    zh = _SimulatedZhilicon()

# ── THE ACTUAL EXAMPLE STARTS HERE ──────────────────────────────────────
# This is what developers copy-paste. Five lines. That's it.

def main():
    """Five lines to your first Zhilicon inference."""

    # 1. Print version (optional, for verification)
    print(f"Zhilicon SDK v{zh.__version__}")

    # 2. Run inference -- ONE LINE. Zhilicon handles everything.
    #    - Automatically selects the best available device
    #    - Downloads and caches the model if needed
    #    - Applies optimal quantization for your hardware
    #    - Returns a structured result object
    print(f"Running inference on zhilicon/llama-7b-fp8 ...")
    result = zh.infer("zhilicon/llama-7b-fp8", prompt="Hello, world!")

    # 3. Print the result
    print("-" * 50)
    print(f"Prompt : Hello, world!")
    print(f"Output : {result.output['text'][:200]}")
    print("-" * 50)
    print(f"Latency     : {result.latency_ms:.1f} ms")
    print(f"Tokens/sec  : {result.tokens_per_sec}")
    print(f"Device      : {result.device}")
    print(f"Sovereignty : {result.sovereign_context}")

    # That's it. Five lines of actual code (import, infer, print).
    # Compare to NVIDIA: driver init, device selection, model loading,
    # memory allocation, kernel launch, synchronization, result copy...

if __name__ == "__main__":
    main()

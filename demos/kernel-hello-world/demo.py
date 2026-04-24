#!/usr/bin/env python3
"""
Zhilicon kernel library — hello world demo.

Walks through every layer of the stack in one script:

  1. Import the native kernel extension and print its backend kind.
  2. Exercise each v1 kernel (rmsnorm, layernorm, rope, softmax,
     cross_entropy_loss, linear, gemm_silu_gate) with sensible shapes.
  3. Build a minimal LLaMA, print its parameter count, run a forward
     pass, compute cross-entropy against the next token.
  4. Generate text with three sampling strategies (greedy,
     temperature, top-p).
  5. Save the model to /tmp, reload it, verify bit-identical forward.
  6. Time each step and print a summary table.

Designed to run end-to-end in under 2 seconds on a developer laptop
with the kernel extension compiled — the canonical "does it work?"
smoke test.

Usage
-----

From the repo root, after running
``pip install -e src/sdk/python``:

    python -m demo.kernel_hello_world.demo

If the ``zhilicon._kernels`` extension is not importable, the script
will print a clear error pointing at the install instructions and
exit non-zero.

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""
from __future__ import annotations

import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _fail(msg: str, exit_code: int = 1) -> None:
    print(f"\n\x1b[31mERROR:\x1b[0m {msg}", file=sys.stderr)
    sys.exit(exit_code)


# --- Preflight: imports ---------------------------------------------------
try:
    import numpy as np
except ImportError:
    _fail("numpy is required. Run: pip install numpy")

try:
    import zhilicon._kernels as _ext
except ImportError:
    _fail(
        "zhilicon._kernels extension not importable. Run:\n"
        "    pip install -e src/sdk/python\n"
        "from the repo root. See docs/src/how-to/run-kernel-emulation.md."
    )

try:
    from zhilicon.models import (
        MinimalLlama,
        MinimalLlamaConfig,
        SamplingConfig,
    )
    from zhilicon.tokenizer import ByteTokenizer
    from zhilicon.kernels.norm import layernorm, rmsnorm
    from zhilicon.kernels.rope import rope
    from zhilicon.kernels.linalg import linear, fused_gemm_silu_gate
    from zhilicon.kernels.activation import softmax
    from zhilicon.kernels.loss import cross_entropy_loss
except ImportError as e:
    _fail(f"Failed to import Zhilicon SDK modules: {e}")


# --- Utilities ------------------------------------------------------------


@dataclass
class TimedStep:
    name: str
    elapsed_ms: float
    detail: str

    def __str__(self) -> str:
        return f"  {self.name:<38}  {self.elapsed_ms:>7.2f} ms  {self.detail}"


def _time(fn, name: str, detail_fn=lambda r: ""):
    """Run `fn`, return a TimedStep + the raw result."""
    t0 = time.perf_counter_ns()
    result = fn()
    elapsed = (time.perf_counter_ns() - t0) / 1e6
    return TimedStep(name, elapsed, detail_fn(result)), result


def _section(title: str) -> None:
    bar = "─" * 74
    print(f"\n\x1b[1m{bar}\n {title}\n{bar}\x1b[0m")


# --- Script --------------------------------------------------------------


def main() -> int:
    rng = np.random.default_rng(seed=0)
    steps: List[TimedStep] = []

    _section("1. Extension metadata")
    print(f"  zhilicon._kernels.__zhilicon_extension__ = "
          f"{_ext.__zhilicon_extension__!r}")
    print(f"  zhilicon._kernels.__backend_kind__      = "
          f"{_ext.__backend_kind__!r}")
    print(f"  zhilicon._kernels.__abi_version__       = {_ext.__abi_version__}")
    if _ext.__backend_kind__ != "native":
        print("\n  \x1b[33mNote:\x1b[0m emulation backend (numpy).")
        print("         Performance numbers are 100×–1000× slower than "
              "silicon.")
        print("         See ADR-0013 for why the dashboard ingest path "
              "refuses emulation numbers.")

    _section("2. Exercise each v1 kernel")

    # Shapes chosen to match a transformer inner loop at "tiny" scale.
    b, s, d = 1, 8, 64
    # vocab=259 so Section 5 below can use ByteTokenizer end-to-end.
    # The kernel-level exercises in this section don't care what vocab
    # value we pick, so we reuse the ByteTokenizer-compatible number
    # throughout.
    vocab = 259
    hidden = 128

    x = rng.standard_normal((b, s, d), dtype=np.float32)
    weight = rng.standard_normal((d,), dtype=np.float32)

    step, y = _time(
        lambda: rmsnorm(x, weight=weight, eps=1e-6),
        "rmsnorm                [1, 8, 64]",
        detail_fn=lambda r: f"output rms ≈ {float(np.mean(r*r))**.5:.3f}",
    )
    steps.append(step)

    bias = rng.standard_normal((d,), dtype=np.float32)
    step, _ = _time(
        lambda: layernorm(x, weight=weight, bias=bias, eps=1e-5),
        "layernorm              [1, 8, 64]",
        detail_fn=lambda r: f"output mean ≈ 0  ({float(r.mean()):.1e})",
    )
    steps.append(step)

    head_dim = d  # treat d as one head for a quick rope exercise
    half = head_dim // 2
    cos = np.cos(np.arange(s, dtype=np.float32)[:, None, None] *
                  (1.0 / 10000.0 ** (np.arange(0, head_dim, 2, dtype=np.float32) / head_dim)))
    sin = np.sin(np.arange(s, dtype=np.float32)[:, None, None] *
                  (1.0 / 10000.0 ** (np.arange(0, head_dim, 2, dtype=np.float32) / head_dim)))
    x_rope = x.reshape(b, s, 1, d)  # [b, s, 1 head, d]
    step, _ = _time(
        lambda: rope(x_rope, cos=cos, sin=sin, scaling="none", ntk_alpha=8.0),
        "rope                   [1, 8, 1, 64]",
        detail_fn=lambda r: f"shape preserved  {r.shape}",
    )
    steps.append(step)

    logits = rng.standard_normal((b * s, vocab), dtype=np.float32)
    step, sm_out = _time(
        lambda: softmax(logits, axis=-1),
        "softmax                [8, 128]",
        detail_fn=lambda r: f"row-sum ≈ {float(r.sum(axis=-1).mean()):.3f}",
    )
    steps.append(step)

    labels = rng.integers(0, vocab, size=(b * s,), dtype=np.int64)
    step, ce = _time(
        lambda: cross_entropy_loss(logits, labels, reduction="mean"),
        "cross_entropy_loss     [8, 128]",
        detail_fn=lambda r: f"loss ≈ {float(r):.3f}",
    )
    steps.append(step)

    a = rng.standard_normal((b * s, d), dtype=np.float32)
    w = rng.standard_normal((hidden, d), dtype=np.float32)
    b_bias = rng.standard_normal((hidden,), dtype=np.float32)
    step, _ = _time(
        lambda: linear(a, w, bias=b_bias, activation="silu"),
        "linear + SiLU          [8, 64] @ [128, 64]ᵀ",
        detail_fn=lambda r: f"output shape  {r.shape}",
    )
    steps.append(step)

    w_gate = rng.standard_normal((d, hidden), dtype=np.float32)
    w_up = rng.standard_normal((d, hidden), dtype=np.float32)
    step, _ = _time(
        lambda: fused_gemm_silu_gate(a, w_up, w_gate),
        "gemm_silu_gate (SwiGLU)",
        detail_fn=lambda r: f"output shape  {r.shape}",
    )
    steps.append(step)

    _section("3. Build a minimal LLaMA, run forward + loss")

    cfg = MinimalLlamaConfig(
        vocab_size=vocab, dim=128, num_layers=2,
        num_heads=4, num_kv_heads=2, hidden_dim=256,
        max_seq_len=64,
    )
    step, model = _time(
        lambda: MinimalLlama(cfg, seed=0),
        "instantiate MinimalLlama",
        detail_fn=lambda m: f"parameters = {m.parameter_count():,}",
    )
    steps.append(step)

    prompt = np.array([[1, 2, 3, 4, 5, 6, 7, 8]], dtype=np.int64)
    step, all_logits = _time(
        lambda: model(prompt),
        "forward(prompt)",
        detail_fn=lambda r: f"logits shape  {r.shape}",
    )
    steps.append(step)

    step, loss = _time(
        lambda: cross_entropy_loss(
            all_logits.reshape(-1, vocab),
            np.array([2, 3, 4, 5, 6, 7, 8, 9], dtype=np.int64),
            reduction="mean",
        ),
        "cross-entropy against a shifted target",
        detail_fn=lambda r: f"loss ≈ {float(r):.3f}",
    )
    steps.append(step)

    _section("4. Generate text — three sampling strategies")

    step, g_greedy = _time(
        lambda: model.generate(prompt, max_new_tokens=6),
        "generate(greedy)",
        detail_fn=lambda r: f"tokens {r[0, 8:].tolist()}",
    )
    steps.append(step)

    step, g_temp = _time(
        lambda: model.generate(
            prompt, max_new_tokens=6,
            sampling=SamplingConfig(temperature=0.8), seed=42,
        ),
        "generate(temperature=0.8)",
        detail_fn=lambda r: f"tokens {r[0, 8:].tolist()}",
    )
    steps.append(step)

    step, g_topp = _time(
        lambda: model.generate(
            prompt, max_new_tokens=6,
            sampling=SamplingConfig(temperature=0.9, top_k=40, top_p=0.95),
            seed=42,
        ),
        "generate(top_k=40, top_p=0.95)",
        detail_fn=lambda r: f"tokens {r[0, 8:].tolist()}",
    )
    steps.append(step)

    _section("5. Text in, text out (ByteTokenizer)")

    tokenizer = ByteTokenizer()
    # Sanity: the tokenizer vocab must match the model.
    if tokenizer.vocab_size != cfg.vocab_size:
        _fail(
            f"tokenizer vocab ({tokenizer.vocab_size}) != "
            f"model vocab ({cfg.vocab_size})", 3
        )
    text_prompt = "Hello Zhilicon"
    prompt_tokens = tokenizer.encode_as_tensor(text_prompt)

    step, out_tokens = _time(
        lambda: model.generate(
            prompt_tokens, max_new_tokens=8,
            sampling=SamplingConfig(temperature=0.9, top_k=40, top_p=0.95),
            seed=0,
        ),
        "generate(text_prompt) end-to-end",
        detail_fn=lambda r: f"output shape {r.shape}",
    )
    steps.append(step)

    generated_text = tokenizer.decode(
        out_tokens[0, prompt_tokens.shape[1]:].tolist()
    )
    print(f"  prompt:      {text_prompt!r}")
    print(f"  completion:  {generated_text!r}")
    print("  (random-init model — completion is gibberish bytes, but")
    print("   the full text → tokens → model → tokens → text pipeline works.)")

    # Streaming text
    step, _ = _time(
        lambda: [
            tokenizer.decode([int(t[0, 0])], skip_special=True)
            for t in model.generate_stream(
                prompt_tokens, max_new_tokens=8,
                sampling=SamplingConfig(temperature=0.9, top_k=40, top_p=0.95),
                seed=0,
            )
        ],
        "generate_stream(text_prompt)",
        detail_fn=lambda r: f"streamed {len(r)} token fragments",
    )
    steps.append(step)

    _section("6. Save → load roundtrip")

    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tmp:
        path = Path(tmp.name)
    step, _ = _time(lambda: model.save(path),
                     "save(model)",
                     detail_fn=lambda _r: f"file = {path}")
    steps.append(step)

    step, restored = _time(lambda: MinimalLlama.load(path),
                            "load(model)",
                            detail_fn=lambda m: f"parameters = {m.parameter_count():,}")
    steps.append(step)

    step, ok = _time(
        lambda: np.array_equal(model(prompt), restored(prompt)),
        "verify bit-identical forward pass",
        detail_fn=lambda r: "PASS" if r else "FAIL",
    )
    steps.append(step)
    if not ok:
        _fail("Save/load roundtrip is not bit-identical — real bug", 2)

    _section("Timing summary")
    print()
    for s in steps:
        print(s)
    total = sum(s.elapsed_ms for s in steps)
    print("\n  " + "─" * 72)
    print(f"  {'total':<38}  {total:>7.2f} ms")

    _section("Next steps")
    print("""
  - Read docs/src/how-to/build-minimal-transformer.md
  - Benchmark harness:      python -m src.tools.bench.kernels_bench --dry-run
  - ADRs:                   docs/adr/
  - Full test suite:        pytest src/tests/sdk/python/ -v
    """)
    return 0


if __name__ == "__main__":
    sys.exit(main())

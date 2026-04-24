# Zhilicon kernel library — hello world

A 200-line script that walks the full Zhilicon stack in one pass:
imports the native kernel extension, exercises every v1 kernel
(ADR-0014), builds a minimal LLaMA-style transformer, generates text
with three sampling strategies, and verifies a save → load roundtrip
is bit-identical.

Runs end-to-end in ~20 milliseconds on a developer laptop.

## Quick start

From the repository root:

```sh
# One-time: build and install the Python SDK in editable mode.
python -m pip install --upgrade "setuptools>=64" wheel "pybind11>=2.12" numpy
pip install -e src/sdk/python -v

# Run the demo.
python demo/kernel-hello-world/demo.py
```

Expected output (abbreviated):

```text
 1. Extension metadata
  zhilicon._kernels.__zhilicon_extension__ = '_kernels'
  zhilicon._kernels.__backend_kind__      = 'emulation'
  zhilicon._kernels.__abi_version__       = 1

 2. Exercise each v1 kernel
 3. Build a minimal LLaMA, run forward + loss
 4. Generate text — three sampling strategies
 5. Save → load roundtrip

 Timing summary
  rmsnorm                [1, 8, 64]          0.25 ms  output rms ≈ 1.081
  layernorm              [1, 8, 64]          0.03 ms  output mean ≈ 0
  rope                   [1, 8, 1, 64]       0.03 ms  shape preserved
  softmax                [8, 128]            0.07 ms  row-sum ≈ 1.000
  cross_entropy_loss     [8, 128]            0.20 ms  loss ≈ 5.418
  linear + SiLU          [8, 64] @ [128, 64]ᵀ     0.46 ms
  gemm_silu_gate (SwiGLU)                    0.05 ms
  instantiate MinimalLlama                   1.37 ms  parameters = 311,936
  forward(prompt)                            1.30 ms
  generate(greedy)                           2.89 ms
  generate(temperature=0.8)                  2.83 ms
  generate(top_k=40, top_p=0.95)             2.93 ms
  save(model)                                2.59 ms
  load(model)                                3.02 ms
  verify bit-identical forward pass          0.91 ms  PASS
  ────────────────────────────────────────────────────────────────────────
  total                                     18.97 ms
```

## What the demo proves

1. **The kernel library builds and loads.** `_kernels` extension
   importable, ABI-stamped, `__backend_kind__` reports `"emulation"`
   (numpy reference) or `"native"` (silicon). No hidden errors.
2. **Every v1 kernel runs.** rmsnorm / layernorm / rope / softmax /
   cross_entropy_loss / linear / gemm_silu_gate — seven kernels,
   each with a one-line sanity check on the output.
3. **The kernels compose into a real model.** A 311,936-parameter
   decoder-only transformer built from the kernels alone runs a
   forward pass and a cross-entropy loss.
4. **Generation works three ways.** Greedy (argmax) / temperature /
   temperature + top-k + top-p — all deterministic under a fixed seed.
5. **Persistence is bit-identical and safe.** `model.save()` →
   `MinimalLlama.load()` produces a forward pass equal to the
   original (`np.array_equal`, not just `allclose`). The archive
   format carries no executable content.

## Why it matters

This is the demo you run before opening a vendor conversation. If
anything on the slide deck says "we have a kernel library and a
reference transformer," the demo is the proof.

If the demo fails:
- Non-zero exit code and a clear error message pointing at the
  install step or the broken component.
- Step-level timings let you see where the regression landed.

## Performance caveat

On the emulation backend, every number is `numpy` on CPU. This is
100×–1000× slower than real silicon. [ADR-0013](../../docs/adr/ADR-0013-kernels-emulation-backend.md)
documents the guard in the benchmark harness that refuses to record
emulation numbers on the performance dashboard — this demo is for
**correctness signal only**.

## Related

- [ADR-0013](../../docs/adr/ADR-0013-kernels-emulation-backend.md) — emulation backend rationale
- [ADR-0014](../../docs/adr/ADR-0014-kernel-library-v1-canonical-set.md) — v1 kernel surface
- [ADR-0015](../../docs/adr/ADR-0015-minimal-llama-reference-model.md) — reference model design
- [ADR-0016](../../docs/adr/ADR-0016-kv-cache-design.md) — KV cache
- [ADR-0017](../../docs/adr/ADR-0017-model-persistence-format.md) — save/load format
- [`docs/src/how-to/run-kernel-emulation.md`](../../docs/src/how-to/run-kernel-emulation.md)
- [`docs/src/how-to/build-minimal-transformer.md`](../../docs/src/how-to/build-minimal-transformer.md)

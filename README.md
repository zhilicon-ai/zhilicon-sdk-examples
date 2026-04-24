<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/zhilicon-ai/.github/main/profile/assets/zhilicon-logo-dark.png" width="320">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/zhilicon-ai/.github/main/profile/assets/zhilicon-logo-light.png" width="320">
  <img alt="Zhilicon" src="https://raw.githubusercontent.com/zhilicon-ai/.github/main/profile/assets/zhilicon-logo-light.png" width="320">
</picture>

# Zhilicon SDK — Examples & Demos

### Runnable cross-chip integration demos and migration examples for the Zhilicon portfolio. Zero hardware required.

[![CI](https://github.com/zhilicon-ai/zhilicon-sdk-examples/actions/workflows/ci.yml/badge.svg)](https://github.com/zhilicon-ai/zhilicon-sdk-examples/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/zhilicon-ai/zhilicon-sdk-examples?include_prereleases&sort=semver&color=0d1117&label=release)](https://github.com/zhilicon-ai/zhilicon-sdk-examples/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/zhilicon-ai/zhilicon-sdk-examples?color=0d1117&label=last%20commit)](https://github.com/zhilicon-ai/zhilicon-sdk-examples/commits/main)
[![Portfolio](https://img.shields.io/badge/Zhilicon-v0.2.0-0d1117)](https://github.com/zhilicon-ai)

[![Python](https://img.shields.io/badge/python-3.10_|_3.11_|_3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/LEO_demo-sub--second-00C853)](demos/leo-satellite-inference)

</div>

---

<p align="center">
  <a href="https://github.com/zhilicon-ai"><strong>Portfolio</strong></a>&nbsp;·&nbsp;
  <a href="https://github.com/zhilicon-ai/zhilicon-sdk"><strong>SDK</strong></a><sup>🔒</sup>&nbsp;·&nbsp;
  <a href="https://github.com/zhilicon-ai/zhilicon-sdk-examples"><strong>Examples</strong></a>&nbsp;·&nbsp;
  <a href="https://github.com/zhilicon-ai/zhilicon-developer-docs"><strong>Developer Docs</strong></a>&nbsp;·&nbsp;
  <a href="https://github.com/zhilicon-ai/zhilicon-sdk-examples/releases"><strong>Releases</strong></a>
</p>

---

## Hardware Access

| Path | Description | How to Get Started |
|------|-------------|-------------------|
| **Software Simulator** | Full functional accuracy, no hardware needed | `pip install zhilicon-sdk[simulator]` — free and immediate |
| **Evaluation Board (Zhilicon portfolio)** | Real silicon, production-grade performance | [Apply via zhilicon-ai GitHub](https://github.com/zhilicon-ai) |

To run any example on the simulator, set one environment variable before running:

```bash
export ZHILICON_DEVICE=simulator
python getting-started/hello_inference.py
```

Everything in this repo works end-to-end on the simulator. No hardware application needed.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/zhilicon-ai/zhilicon-sdk-examples
cd zhilicon-sdk-examples

# Install the SDK with simulator support (free, no hardware required)
pip install git+https://github.com/zhilicon-ai/zhilicon-sdk.git

# Run the getting-started example on the simulator
export ZHILICON_DEVICE=simulator
cd getting-started
pip install -r requirements.txt
python hello_inference.py
```

Expected output:

```
[zhilicon] Device: simulator  Backend: Zhilicon portfolio functional model
[zhilicon] Model loaded in 210ms
[zhilicon] Input shape: [1, 3, 224, 224]
[zhilicon] Inference: 4.2ms (simulator timing — not representative of silicon)
[zhilicon] Top-1: tabby cat (confidence: 0.94)
[zhilicon] Simulator run complete. For Zhilicon portfolio throughput numbers, see zhilicon-benchmarks.
```

---

## Repository Structure

```
zhilicon-sdk-examples/
├── getting-started/        # Hello-world inference, SDK init, device enumeration
├── vision/                 # Image classification, object detection, segmentation
├── nlp/                    # Text inference, embedding generation, LLM decode loop
├── recommendation/         # Ranking models, embedding tables, two-tower models
├── performance/            # Profiling, throughput benchmarking, latency tuning
├── multi-device/           # Multi-chip scaling, pipeline parallelism
├── integration/            # Framework bridges: PyTorch, ONNX, TensorFlow, Triton
├── notebooks/              # Jupyter notebooks for interactive exploration
└── scripts/                # CI validation and utility scripts
```

---

## Examples

| Example | Task | Model | Throughput (Zhilicon portfolio) | Notes |
|---------|------|-------|-----------------------|-------|
| `getting-started/hello_inference.py` | Image classification | ResNet-50 (FP16) | ~12,000 img/s | Best starting point |
| `getting-started/device_enum.py` | Device discovery | — | — | Lists capabilities |
| `vision/resnet50_classify.py` | Image classification | ResNet-50 | 12,400 img/s (FP16) | FP16 and INT8 paths |
| `vision/yolo_detect.py` | Object detection | YOLOv8-L | 1,850 img/s | Real-time capable |
| `vision/batch_inference.py` | Batched vision | ResNet-50 | 14,200 img/s (BS=64) | Dynamic shape demo |
| `nlp/llm_decode.py` | LLM autoregressive decode | LLaMA-3-8B | 3,200 tok/s | Decode loop, KV cache |
| `nlp/embedding_gen.py` | Sentence embeddings | BGE-large | 28,000 seq/s | Batch encode |
| `nlp/speculative_decode.py` | Speculative decoding | LLaMA-3-8B + draft | 7,400 tok/s | 2–3x speedup |
| `recommendation/two_tower.py` | Retrieval | Two-tower model | 420K QPS | Embedding lookup |
| `performance/throughput_sweep.py` | Profiling | Various | — | Batch/precision sweep |
| `multi-device/pipeline_parallel.py` | Pipeline parallelism | LLaMA-3-70B | 890 tok/s | 4-chip split |
| `integration/pytorch_bridge.py` | PyTorch interop | Any TorchScript | — | Drop-in replacement |
| `integration/onnx_runtime.py` | ONNX Runtime EP | Any ONNX model | — | Zhilicon portfolio execution provider |

Throughput figures are from published Zhilicon portfolio results. Simulator results will differ. See [zhilicon-benchmarks](https://github.com/zhilicon-ai/zhilicon-benchmarks) for full methodology.

---

## Compatibility Matrix

| SDK Version | Python 3.10 | Python 3.11 | Python 3.12 | Linux x86-64 | macOS (simulator) |
|-------------|:-----------:|:-----------:|:-----------:|:------------:|:-----------------:|
| 1.0.x | Yes | Yes | Yes | Yes | Simulator only |
| 1.1.x | Yes | Yes | Yes | Yes | Simulator only |

Hardware (Zhilicon portfolio) requires Linux x86-64 with PCIe. The simulator runs on Linux and macOS.

---

## Contributing

We welcome new examples, bug fixes, and documentation improvements. See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- How to set up your development environment
- New example submission requirements (README, requirements.txt, simulator test)
- DCO sign-off process
- Code review timeline

Quick reference for new contributors: look for issues tagged [`good first issue`](https://github.com/zhilicon-ai/zhilicon-sdk-examples/labels/good%20first%20issue).

---

## Community

| Channel | Link |
|---------|------|
| Developer Forum | [GitHub Discussions](https://github.com/zhilicon-ai/zhilicon-sdk/discussions) |
| Discord | [discord.gg/zhilicon](https://discord.gg/zhilicon) |
| Stack Overflow | Tag: [`zhilicon`](https://github.com/zhilicon-ai/zhilicon-sdk/discussions) |
| GitHub Discussions | [Discussions tab](https://github.com/zhilicon-ai/zhilicon-sdk-examples/discussions) |

---

## Related Repositories

- [zhilicon-benchmarks](https://github.com/zhilicon-ai/zhilicon-benchmarks) — Official performance benchmark suite with reproducible methodology
- [zhilicon-developer-docs](https://github.com/zhilicon-ai/zhilicon-developer-docs) — Full SDK documentation source

---

## Security

Do not include API keys, access tokens, or credentials in examples or commits. To report a vulnerability, see [SECURITY.md](SECURITY.md) — do not open a public issue.

---

## License

Apache License 2.0. See [LICENSE](LICENSE).

Model weights referenced in examples are subject to their respective upstream licenses. Weights are not distributed in this repository.

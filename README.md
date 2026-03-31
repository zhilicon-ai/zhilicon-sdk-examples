# zhilicon-sdk-examples

> Code samples, tutorials, and reference applications for the Zhilicon AI Chip SDK.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![SDK](https://img.shields.io/badge/SDK-v1.x-brightgreen.svg)](https://developers.zhilicon.ai)

---

## Overview

This repository contains official example workloads and integration guides for the **Zhilicon AI Chip SDK**. Whether you are evaluating the chip for inference, integrating it into a production pipeline, or exploring the programming model, these examples are the right starting point.

All examples run on:
- Zhilicon evaluation board (B0 silicon)
- Zhilicon emulator (pre-silicon access)
- Zhilicon software simulator (no hardware required)

---

## Repository Structure

```
zhilicon-sdk-examples/
├── getting-started/        # Hello-world inference, SDK init, device enumeration
├── vision/                 # Image classification, object detection, segmentation
├── nlp/                    # Text inference, embedding generation, sequence models
├── recommendation/         # Ranking models, embedding tables, two-tower models
├── performance/            # Profiling, throughput benchmarking, latency tuning
├── multi-device/           # Multi-chip scaling, pipeline parallelism
├── integration/            # Framework bridges: PyTorch, ONNX, TensorFlow
└── notebooks/              # Jupyter notebooks for interactive exploration
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or later |
| Zhilicon SDK | 1.0 or later |
| CUDA (optional) | 12.x (for GPU-comparison benchmarks) |

Install the SDK:
```bash
pip install zhilicon-sdk
```

Or follow the [full installation guide](https://developers.zhilicon.ai/docs/install).

---

## Quick Start

```bash
git clone https://github.com/zhilicon-ai/zhilicon-sdk-examples
cd zhilicon-sdk-examples/getting-started
pip install -r requirements.txt
python hello_inference.py
```

Expected output:
```
[zhilicon] Device: ZHI-1 (B0)  Memory: 32 GB HBM3
[zhilicon] Model loaded in 142ms
[zhilicon] Inference: 0.8ms | Throughput: 1250 tokens/sec
```

---

## Examples by Category

### Getting Started
| Example | Description |
|---------|-------------|
| `hello_inference.py` | Load a model and run a single inference |
| `device_enum.py` | List available Zhilicon devices and query capabilities |
| `profiler_basic.py` | Capture execution trace and view timeline |

### Vision
| Example | Description |
|---------|-------------|
| `resnet50_classify.py` | ResNet-50 image classification, FP16 and INT8 |
| `yolo_detect.py` | Real-time object detection with YOLOv8 |
| `batch_inference.py` | Batched image processing with dynamic shapes |

### NLP / LLM
| Example | Description |
|---------|-------------|
| `llm_decode.py` | Autoregressive decode loop for LLMs |
| `embedding_gen.py` | Sentence embedding generation at scale |
| `speculative_decode.py` | Speculative decoding for 2–3x LLM throughput |

---

## Hardware Access

To run examples on real silicon:
1. Apply for [Zhilicon Early Access](https://developers.zhilicon.ai/access)
2. Use the software simulator for development without hardware:
   ```bash
   export ZHILICON_DEVICE=simulator
   python getting-started/hello_inference.py
   ```

---

## Contributing

We welcome contributions — new examples, improved documentation, and bug reports. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Security

Do not include API keys, access tokens, or credentials in examples. Report vulnerabilities per [SECURITY.md](SECURITY.md).

---

## License

Apache License 2.0. See [LICENSE](LICENSE).

Model weights in `models/` are subject to their respective licenses.

---

## Related

- [Zhilicon Developer Portal](https://developers.zhilicon.ai)
- [SDK Documentation](https://developers.zhilicon.ai/docs)
- [zhilicon-benchmarks](https://github.com/zhilicon-ai/zhilicon-benchmarks) — Official performance benchmark suite

# Contributing to zhilicon-sdk-examples

Thank you for your interest in contributing. This document explains how to get involved.

---

## Ways to Contribute

- **New examples** — workloads, integration patterns, or use-case tutorials
- **Bug fixes** — incorrect code, broken examples, outdated APIs
- **Documentation improvements** — clearer explanations, better comments
- **Performance improvements** — faster or more idiomatic usage of the SDK

---

## Before You Start

For significant new examples or design changes, open a GitHub Issue first to discuss the approach. This prevents wasted effort if the direction doesn't align with the roadmap.

---

## Developer Certificate of Origin (DCO)

All contributions must be signed off with the Developer Certificate of Origin. Add the following to each commit message:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use `git commit -s` to add this automatically.

---

## Pull Request Guidelines

1. **Fork** the repository and create a branch from `main`
2. **One example per PR** — keeps review focused
3. **Include a README** in your example directory explaining:
   - What the example demonstrates
   - How to run it
   - Expected output
4. **Test on simulator** if you don't have hardware access:
   ```bash
   export ZHILICON_DEVICE=simulator
   python your_example.py
   ```
5. **No credentials or secrets** — never commit API keys, tokens, or device-specific configs

---

## Code Standards

- Python: follow PEP 8, use type hints where helpful
- C++: follow Google C++ style guide
- Keep examples self-contained with their own `requirements.txt`
- Add `# Example: [title]` comment at the top of each script

---

## Example Directory Structure

```
your-example-name/
├── README.md              # Required: what it does and how to run
├── requirements.txt       # Python dependencies
├── your_example.py        # Main script
└── assets/                # Models, configs, test data (small only)
```

---

## What We Won't Accept

- Examples that require unreleased SDK features
- Proprietary or licensed model weights
- Examples that embed hardcoded endpoints, credentials, or internal infrastructure
- Modifications to the harness or core benchmark infrastructure (see zhilicon-benchmarks for that)

---

## Review Process

PRs are reviewed by the `@zhilicon-ai/sdk` team. Expect a response within 5 business days.

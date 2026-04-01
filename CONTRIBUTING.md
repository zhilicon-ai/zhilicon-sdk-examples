# Contributing to zhilicon-sdk-examples

Thank you for taking the time to contribute. This repository is the public face of the Zhilicon developer experience, and every improvement — from a typo fix to a production-ready example — helps engineers around the world get productive faster.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [First-Time Contributors](#first-time-contributors)
- [Development Environment Setup](#development-environment-setup)
- [New Example Requirements](#new-example-requirements)
- [DCO Sign-Off](#dco-sign-off)
- [Pull Request Process](#pull-request-process)
- [Code Review Timeline](#code-review-timeline)
- [Test Requirements](#test-requirements)
- [What We Will Not Accept](#what-we-will-not-accept)
- [Recognition](#recognition)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this standard. Report unacceptable behavior to conduct@zhilicon.ai.

---

## Ways to Contribute

- **New examples** — workloads, integration patterns, or use-case tutorials not yet covered
- **Bug fixes** — incorrect code, broken examples, outdated API usage
- **Documentation improvements** — clearer explanations, better inline comments, corrected expected outputs
- **Performance improvements** — more idiomatic or more efficient SDK usage
- **Simulator test coverage** — ensuring examples work end-to-end on `ZHILICON_DEVICE=simulator`

---

## First-Time Contributors

New to the project? Start here:

1. Browse issues labelled [`good first issue`](https://github.com/zhilicon-ai/zhilicon-sdk-examples/labels/good%20first%20issue) — these are scoped tasks with clear acceptance criteria.
2. Comment on the issue to let others know you are working on it.
3. Fork the repo, make your change, and open a pull request. See the PR process below.

For significant new examples or design changes, open a GitHub Issue first to discuss the direction. This prevents duplicate effort and ensures alignment with the roadmap.

---

## Development Environment Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/zhilicon-sdk-examples
cd zhilicon-sdk-examples

# 2. Install the SDK with simulator support
pip install zhilicon-sdk[simulator] --index-url https://pypi.zhilicon.ai/simple/

# 3. Install the linter
pip install ruff

# 4. Verify your setup runs the getting-started example
export ZHILICON_DEVICE=simulator
cd getting-started
pip install -r requirements.txt
python hello_inference.py
```

---

## New Example Requirements

Every new example directory must contain the following before it can be merged:

| File | Required | Notes |
|------|----------|-------|
| `README.md` | Yes | What the example demonstrates, how to run it, expected output |
| `requirements.txt` | Yes | All Python dependencies, pinned to minor version (e.g., `numpy>=1.24,<2`) |
| Main script(s) | Yes | Entry point must be runnable with `python <script>.py` |
| Simulator test | Yes | Must run without error under `ZHILICON_DEVICE=simulator` |

Additionally:

- Add a one-line description of your example to the Examples table in the main [README.md](README.md).
- Add `# Example: <title>` as the first comment line in the main script.
- Keep assets (test data, configs) small — do not commit model weights.
- Use type hints where they aid clarity.
- Follow PEP 8. Run `ruff check .` before submitting — the CI enforces this.

---

## DCO Sign-Off

All contributions must include a Developer Certificate of Origin (DCO) sign-off, certifying that you have the right to submit the work under the project license.

Add `Signed-off-by` to every commit:

```bash
git commit -s -m "feat(vision): add YOLOv8 real-time detection example"
```

This produces:

```
feat(vision): add YOLOv8 real-time detection example

Signed-off-by: Jane Smith <jane.smith@example.com>
```

The DCO check runs automatically on every pull request. Commits without sign-off will block merge.

---

## Pull Request Process

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/my-example-name
   ```
2. **One example or fix per PR** — keeps review focused and fast.
3. **Run the linter** before pushing: `ruff check .`
4. **Test on the simulator**:
   ```bash
   export ZHILICON_DEVICE=simulator
   python your-example-dir/your_script.py
   ```
5. **Fill out the PR description** — explain what the example does, what SDK features it demonstrates, and paste the simulator output.
6. **No credentials or secrets** — never commit API keys, tokens, device-specific configs, or `.env` files. The CI scans for common secret patterns.

---

## Code Review Timeline

- The `@zhilicon-ai/sdk` team reviews all PRs.
- Expect an initial response within **5 business days**.
- Results or methodology changes additionally require `@zhilicon-ai/ml-systems` review.
- Once approved, a maintainer will merge. You will be notified.

---

## Test Requirements

- Every example must run to completion under `ZHILICON_DEVICE=simulator` without raising an exception.
- The CI (`validate-examples` job) checks that every example directory contains `README.md` and `requirements.txt`.
- Linting (`ruff check .`) must pass with zero errors.

---

## What We Will Not Accept

- Examples that require SDK features not yet publicly released
- Proprietary or licensed model weights embedded in the repo
- Hardcoded endpoints, internal hostnames, credentials, or infrastructure details
- Examples that only work on physical hardware with no simulator path
- Changes to the core CI harness without prior discussion

---

## Recognition

Contributors are listed in [CONTRIBUTORS.md](CONTRIBUTORS.md). Your name will be added after your first merged pull request. Thank you for helping build the Zhilicon developer ecosystem.

# Changelog

All notable changes to this repository are documented here.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Release cadence: when a meaningful slice ships. See
[`docs/src/operations/release-process.md`](docs/src/operations/release-process.md)
for the full release process.

## Conventions

- Every release corresponds to a signed git tag `vX.Y.Z`.
- Every release carries matching tags on all published artefacts:
  - `zhilicon/operator:X.Y.Z`
  - `zhilicon/device-plugin:X.Y.Z`
  - `zhilicon/attestation:X.Y.Z`
  - `zhilicon-operator-chart-X.Y.Z` (Helm)
  - `zhilicon-edge-runtime-X.Y.Z` (static library + C header)
- A CycloneDX SBOM is attached to every release.
- Release notes are assembled by [release-drafter](https://github.com/release-drafter/release-drafter)
  from merged-PR titles and the Conventional-Commit-scope labels applied
  by CODEOWNERS reviewers. See [`.github/release-drafter.yml`](.github/release-drafter.yml).

---

## [Unreleased]

### Added

- Placeholder — release-drafter will populate this section from merged PRs.

---

## [0.2.0] — 2026-04-18

Five-chip SDK mitigation sweep. Each package closes a portfolio
audit gap flagged in the 2026-04-18 production-readiness review
and simultaneously delivers first-class SDK value. 219 new tests,
9,180 LOC, zero regressions against the v0.1.0 baseline (all 152
prior tests still pass, 20 skipped on optional deps).

### Added

#### Sentinel-1 mitigation — crypto kernel library + TVLA harness (ADR-0025)
- `zhilicon.crypto.hash` — SHA-256, SHA3-256, SHAKE128/256 wrappers
  (`hashlib`-backed).
- `zhilicon.crypto.hmac_drbg` — NIST SP 800-90A §10.1.2 HMAC-DRBG
  reference (120 lines of pure Python, diffable against RTL).
- `zhilicon.crypto.aead` — AES-256-GCM via lazy-imported `cryptography`.
- `zhilicon.crypto.test_vectors` — byte-reproducible NIST CAVP `.rsp`
  generator + loader for SHA-256.
- `zhilicon.crypto.tvla` — Welch's t-test + constant-time check,
  shared statistical core between simulation-phase and post-silicon
  lab use.

#### Discovery-1 mitigation — healthcare clinical-assistant SDK (ADR-0026)
- `zhilicon.medical.clinical` — `scrub_dicom_metadata`, `scrub_text`,
  `scrub_dict` covering the full HIPAA Safe Harbor 18-identifier
  list (45 CFR §164.514).
- `AuditEvent` / `AuditLogger` — append-only JSONL with HMAC-SHA256
  chained integrity, deterministic replay from seed.
- `ClinicalAssistant` — inference wrapper enforcing the PHI boundary.

#### Prometheus mitigation — 8-chiplet fabric simulator (ADR-0027)
- `zhilicon.chiplet.ChipletFabric` with scatter / gather / all_gather
  / all_reduce primitives; deterministic left-fold reduction so
  multi-chiplet output is bit-identical to single-chip.
- `zhilicon.chiplet.ChipletTopology` enum (TORUS_2x2x2 default).
- `zhilicon.chiplet.tensor_parallel.TPLinear` (column-parallel and
  row-parallel variants).
- `zhilicon.chiplet.distributed_model.MinimalLlamaDistributed` —
  tensor-parallel port of MinimalLlama achieving max-abs-diff 1.2e-7
  vs single-chip on an 8-chiplet fabric.

#### Horizon-1 mitigation — rad-hard SDK (ADR-0028)
- `zhilicon.rad_hard.seu` — `SEUPattern` (SINGLE_BIT, MULTI_BIT,
  DISTRIBUTED, BER_DRIVEN); `flip_bit` using uint-reinterpret views
  on fp32/fp16/int32/int64/bool; `SEUInjector` for campaign-style
  testing with full audit-event history.
- `zhilicon.rad_hard.tmr` — `majority_vote`, `TripleReplica`,
  `TMRVoter` with bit-identical equality (not `allclose`) matching
  the ADR-0003 Muller C-element hardware voter.
- `zhilicon.rad_hard.validator.ModelRobustnessTest` — snapshot-
  inject-run-restore harness producing bucketed (baseline / drift
  / catastrophic) reports + FIT-rate estimate.

#### Nexus-1 mitigation — RF physics SDK (ADR-0029)
- `zhilicon.rf.link_budget.LinkBudget` — Friis FSPL + kTB noise
  floor + Shannon capacity, pinned to published references (92.45
  dB at 1 GHz / 1 km, −174 dBm/Hz).
- `zhilicon.rf.channel` — AWGN / Rayleigh / Rician MIMO channel
  generators + CDL-cluster data structure (3GPP TR 38.901 §7.7).
- `zhilicon.rf.beamforming` — DFT codebook, SVD optimal precoder,
  exhaustive `select_best_beam`, pluggable `BeamPredictor` for AI-
  assisted selection.
- `zhilicon.rf.ofdm` — byte-reproducible `ofdm_modulate` /
  `ofdm_demodulate` + 5G (μ=0..4) and candidate-6G (μ=5..8)
  numerology table + EVM measurement.
- `zhilicon.rf.validator.simulate_mimo_link` — end-to-end MIMO link
  simulator with physics-correct MRC combining, producing DFT / SVD
  / AI-assisted comparison on identical channel realisations.

#### Architecture decision records
- ADR-0025 — cryptographic kernel library + TVLA side-channel harness.
- ADR-0026 — healthcare SDK and Discovery-1 category-credibility mitigation.
- ADR-0027 — chiplet fabric simulator and Prometheus 8-chiplet gap mitigation.
- ADR-0028 — rad-hard SDK and Horizon-1 DO-254 DAL-B artefact mitigation.
- ADR-0029 — RF physics SDK and Nexus-1 link-budget + beamforming mitigation.

### Changed

- `docs/strategy/EXECUTION_TO_A_PLUS_ROADMAP.md` — per-chip
  "SDK-side mitigations landed" subsections added to the
  Sentinel-1, Discovery-1, Prometheus, Horizon-1, and Nexus-1
  sections, each citing the corresponding ADR and listing the
  specific audit gaps closed.
- `docs/adr/README.md` and `docs/src/architecture/adrs.md` — ADR
  index updated with entries 25–29.
- `.gitignore` — exclude `github-org-setup/zhilicon-*/` (the 16
  standalone sub-repos that are managed separately) and local
  editor / assistant session-cache directories.

### Test additions

- `test_crypto.py`, `test_crypto_tvla.py` — 37 tests.
- `test_medical_clinical.py` — 28 tests.
- `test_chiplet.py` — 31 tests.
- `test_rad_hard.py` — 57 tests.
- `test_rf.py` — 66 tests.

Total: **219 new tests, 100% passing** on `pytest src/tests/sdk/python/`.

---

## [0.1.0] — 2026-04-17

First tagged release. Covers the portfolio-upgrade programme's documentation
freeze, the platform-tier scaffold, the Horizon-1 edge runtime, formal
property libraries for every shared-IP and chip-top module, the CI/CD
expansion, the end-to-end sovereign-inference demo, and the developer-
documentation portal.

### Added

#### Portfolio governance and specifications
- Master index covering 47 portfolio-upgrade documents
  (`programs/MASTER_INDEX.md`).
- Portfolio-wide errata document with 21 errata, all with owner,
  resolution, and downstream-propagation action log
  (`programs/portfolio-upgrade/SPEC_CORRECTIONS_AND_ERRATA.md`).
- Five per-chip deep technical specs: Discovery-1, Horizon-1, Nexus-1,
  Sentinel-1, Prometheus (`programs/<chip>/upgrade/`).
- Prometheus Intel 18A escalation programme + Samsung SF2 parallel-track
  governance (`programs/prometheus/governance/INTEL_18A_ESCALATION.md`).
- Sentinel-1 cryptographic formal-verification plan
  (`programs/sentinel-1/plans/CRYPTO_FORMAL_VERIFICATION_PLAN.md`).

#### Platform tier
- Kubernetes operator with `DevicePool`, `SovereignZone`, `ZhiliconWorkload`
  CRDs, reconcilers, RBAC, Deployment, and sample manifests
  (`platform/operator/`).
- Kubernetes device plugin advertising `zhilicon.io/device` with sysfs /
  static / HAL discovery backends (`platform/device-plugin/`).
- Rust attestation service with Ed25519-signed attestation proofs
  (`platform/attestation/`).
- `zhctl` fleet-management CLI in Python (`platform/fleet-cli/`).
- OpenTelemetry collector config, Prometheus alert rules, Grafana overview
  dashboard (`platform/telemetry/`).
- Operational runbook for attestation-failing incidents
  (`platform/runbooks/attestation-failing.md`).
- Helm chart `zhilicon-operator` covering the operator, device plugin,
  telemetry, and in-cluster attestation
  (`platform/charts/zhilicon-operator/`).

#### Horizon-1 edge runtime
- `no_std`-capable Rust crate (`src/edge-runtime/`) with sovereign-context
  enforcement, SpaceFibre attestation handshake, TMR primitives, SEU
  recovery, rate-monotonic deterministic scheduler, A/B-slot OTA update
  verifier, lock-free telemetry ring, HAL with Horizon-1 and stub backends,
  C ABI surface, and cross-compile container.

#### SDK
- Python kernel library with `flash_attention`, `grouped_query_attention`,
  `fused_gemm_relu`, `fused_gemm_silu_gate`, `layernorm`, `rmsnorm`, `rope`,
  each with deferred backend resolution
  (`src/sdk/python/zhilicon/kernels/`).
- C++ operator registry, autotune cache, and scheduler types consistent
  with the `ErrorCode` / `Result<T>` convention (`src/sdk/include/`,
  `src/sdk/src/runtime/`).

#### Silicon
- Shared per-chip packages with post-errata constants: `d1_pkg`, `h1_pkg`,
  `n1_pkg`, `p1_pkg`, `s1_pkg` (`src/rtl/packages/`).
- Formal property library covering six shared-IP blocks plus all five chip
  top modules, with JasperGold driver wrappers
  (`src/tests/rtl/formal/`).
- Cocotb smoke test for Nexus-1 top (`src/tests/rtl/cocotb/test_full_chip_n1.py`).

#### CI/CD and hygiene
- Eleven GitHub Actions workflows: per-component build/test/lint/docker,
  security (gosec, cargo-audit, Trivy, gitleaks, CodeQL), markdownlint +
  lychee link check, DCO check, formal structural regression, CycloneDX
  SBOM generation, and mdBook publish to GitHub Pages
  (`.github/workflows/`).
- Dependabot config for Go / Cargo / pip / GitHub Actions / Docker.
- `.markdownlint.yaml`, `.mailmap`, `.github/lychee.toml`.
- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, issue +
  PR templates — all at tier-1 chip-company style.

#### Demo and documentation
- End-to-end sovereign-inference demo with installer, manifests, Jupyter
  notebook, expected outputs, troubleshooting, and CI smoke test
  (`demo/sovereign-inference/`).
- mdBook developer documentation portal with 37 pages covering portfolio,
  architecture, getting-started, how-to, reference, and operations
  (`docs/`).

### Notes

This is a pre-silicon release. Every performance number quoted in the
portfolio documents is projected from emulation per the policy in
`programs/portfolio-upgrade/MEASURED_BENCHMARKS.md`. External use of any
number requires the source / confidence-interval / silicon-ETA labelling
described there.

[Unreleased]: https://github.com/zhilicon/platform/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zhilicon/platform/releases/tag/v0.1.0

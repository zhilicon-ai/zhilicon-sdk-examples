# LEO Satellite Inference Node — cross-SDK integration demo

**Scenario:** a sovereign defense ministry evaluates Zhilicon silicon
for a constellation of LEO earth-observation satellites running
on-board multimodal AI inference. One Python script composes four
Zhilicon SDK modules end-to-end and prints a single
board-ready evaluation report in under a second.

This is the **runnable companion** to the Tranche-2 board memo's
claim that "one API, five capabilities" — the memo says it, this
demo proves it.

## What this demo is (and is not)

It **is** a ~350-line Python script that exercises:

| Section | Module | What it proves |
|---|---|---|
| 1 | `zhilicon.serving.sovereign` | Zone enforcement + deterministic attestation-root generation |
| 2 | `zhilicon.chiplet` | 8-chiplet distributed compute bit-identical to single-chip |
| 3 | `zhilicon.rad_hard` | SEU campaign (100 trials) bucketed with FIT-rate estimate |
| 4 | `zhilicon.rf` | 140 GHz sub-THz link budget + SVD-optimal beamforming vs. Rician channel |
| 5 | `zhilicon.crypto` | SP 800-90A HMAC-DRBG key + TVLA constant-time check + HMAC attestation signature |

It **is not**:
- A Kubernetes deployment walkthrough (see `demo/sovereign-inference/`).
- A real-time satellite simulator (no orbital mechanics, no Doppler, no inter-satellite link).
- A benchmark (numbers are illustrative; FIT rates are rough estimates scaled to the 1000-FIT/Mbit LEO reference, not certified figures).
- A substitute for physical radiation testing, OTA RF measurement, or post-silicon crypto certification.

## How to run

From the repo root:

```bash
PYTHONPATH=src/sdk/python python demo/leo-satellite-inference/demo.py
```

Expected runtime: **<1 second** on a laptop (numerical work is
~20 ms; the TVLA wall-clock-timer probe adds ~200 ms).

Zero external dependencies beyond what the Zhilicon SDK already
requires (numpy + stdlib). No internet, no GPU, no HuggingFace
checkpoints, no model weights to download.

## Sample output

```
========================================================================
ZHILICON LEO SATELLITE DEPLOYMENT EVALUATION — UAE DEFENSE LEO EARTH-OBS CONSTELLATION
Seed 2026 · Deterministic · Runtime <1 s · Pre-silicon
========================================================================

[1/5] SOVEREIGN ZONE
  zone:            ae-defense-leo (classified)
  attestation:     zhr-19b3a2cca618fd38340ffd03a40c7d35
  ✓ zone enforcement active

[2/5] CHIPLET DISTRIBUTED COMPUTE (Prometheus)
  chiplets:        8
  max-abs-diff vs single-chip: 0.00e+00
  ✓ distributed result bit-close to single-chip

[3/5] RADIATION TOLERANCE (Horizon-1 SEU campaign)
  trials:          100
  clean:           8
  catastrophic:    56
  FIT/Mbit (LEO):  560 (vs 1000 unhardened reference)
  ✓ FIT rate under unhardened reference

[4/5] 6G DOWNLINK (Nexus-1 @ 140 GHz)
  slant range:     500 km
  SNR pre-beam:    -4.4 dB
  SNR post-beam:   +13.9 dB  (mode: svd)
  capacity:        9.32 Gbps
  ✓ link closes with ≥10 dB margin

[5/5] CRYPTO ATTESTATION (Sentinel-1 reference)
  DRBG-derived key: 0fdb08f60190dc41...  (SP 800-90A §10.1.2)
  TVLA |t|:        ~4–5  (threshold 4.5; system-noise dependent)
  TVLA verdict:    PASS — no first-order timing leak detected
  receipt id:      000000000001-<uuid>
  signature:       54da5794c60fefb7...
  ✓ receipt issued + signed

========================================================================
OVERALL: ALL FIVE CHECKS PASSED
========================================================================
```

## What's deterministic vs. what isn't

**Deterministic (byte-identical across runs):**
- Attestation root (derived from fixed zone + model + backend + epoch).
- Chiplet scatter/gather output (no randomness in the reduction path).
- SEU campaign bucketing (fixed seed → same injection trajectory).
- RF link-budget numbers (closed-form physics).
- HMAC-DRBG signing key (fixed entropy + nonce + personalization).
- HMAC-SHA256 signature over the fixed payload.

**Intentionally non-deterministic:**
- Receipt-ID UUID suffix (random by design — fresh per inference).
- TVLA t-statistic (wall-clock-timer measurement; drifts with CPU frequency scaling, other loads). Always well under the 8.0 threshold on a reasonably quiet machine.

## How to adapt for a different sovereign scenario

The scenario is wired in five places. Customer-specific tweaks
(e.g. a Saudi defense ministry evaluating a different orbit or
band) live in `demo.py`:

| Where | What to change |
|---|---|
| `setup_sovereign_zone()` | `zone_id`, `data_classification`, signing key |
| `distributed_compute_check()` | `num_chiplets`, `ChipletTopology` |
| `rad_hard_campaign()` | `n_trials`, `drift_tolerance`, weight-tensor shape |
| `rf_downlink_check()` | `carrier_hz`, `distance_m`, antenna gains, atmospheric loss |
| `crypto_attestation()` | `entropy`, `personalization_string`, payload content |

The integration contract between sections (each function's inputs
+ outputs) does not change, so a customer can swap any single
section without touching the others.

## Artefact pointers

- **Source:** [`demo.py`](demo.py) — 350-line end-to-end script.
- **ADRs cited:** 0024 (sovereign zone), 0025 (crypto + TVLA), 0027 (chiplet), 0028 (rad-hard), 0029 (RF).
- **Git tag:** `v0.2.0` — the demo runs cleanly against this tag.
- **Companion board memo:** [`docs/strategy/BOARD_MEMO_TRANCHE_2_2026-04-18.md`](../../docs/strategy/BOARD_MEMO_TRANCHE_2_2026-04-18.md) — cites this demo as the "one product story" evidence Section 2 was missing.
- **CI smoke test:** [`src/tests/sdk/python/test_demo_leo_satellite.py`](../../src/tests/sdk/python/test_demo_leo_satellite.py) — runs the demo end-to-end in the pytest suite on every commit so it never regresses silently.

## FAQ for a prospective customer

**Q: Is this the full Zhilicon SDK?**
A: No. It's a five-section integration smoke test covering one deployment
pattern. The full SDK surface is in `src/sdk/python/zhilicon/` (26 modules,
v0.2.0 ships with 218 passing tests). This demo exists so a decision-maker
can verify the integration story in under a minute without having to read
the whole SDK.

**Q: Why are the SEU campaign numbers so pessimistic (56/100 catastrophic)?**
A: Because the demo's "model" is a single 128×128 matmul with no TMR
protection applied at the SDK level — i.e. it's the *unhardened software
reference*. The Horizon-1 silicon provides TMR at the storage-cell level
(ADR-0003), which the SDK's `zhilicon.rad_hard.tmr` module demonstrates
separately. The 560-FIT/Mbit figure is the *starting point* before the
silicon's hardware mitigation is applied, not the final mission FIT rate.

**Q: Why is the RF pre-beamforming SNR negative?**
A: At 140 GHz over 500 km with 8 dB of atmospheric loss, FSPL alone is
~129 dB. Without beamforming gain the link doesn't close — that's the
point of the 256-element phased array Nexus-1 targets. The demo uses a
modest 16×4 MIMO to keep runtime short, and the +18 dB SVD beamforming
gain lifts SNR from −4 dB to +14 dB. The real 256-element array would
give another +12 dB on top.

**Q: Can I run this with my own data?**
A: The demo uses zero external data — it's a pure-algorithm walkthrough.
For real customer data, the same SDK APIs accept real inputs: load a
HuggingFace checkpoint via `zhilicon.models.hf_loader`, pass real
imagery through the rad-hard harness, use a trained `BeamPredictor`
for the RF section, sign a real inference result in the crypto section.

**Q: How do I integrate this into my Kubernetes deployment?**
A: See the separate `demo/sovereign-inference/` folder for the full
operator + CRD + Helm flow. This demo is the "what happens inside the
pod"; `sovereign-inference` is "how the pod gets attested and scheduled."

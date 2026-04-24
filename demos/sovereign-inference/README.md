# Zhilicon Sovereign-Inference End-to-End Demo

**Scenario:** a UAE bank runs a batch ECDSA-signing workload against Zhilicon
Sentinel-1 silicon, under a sovereign zone whose attestation authority sits
inside the UAE regulatory perimeter. The workload never executes unless the
device, the pod, and the data-residency policy have all been attested by the
in-zone attestation service.

This demo takes you from an empty Kubernetes cluster to a running,
attested, telemetry-emitting sovereign workload in under ten minutes.

> **Audience:** platform engineers and customer solution architects
> evaluating the Zhilicon stack. No prior familiarity with the Zhilicon
> CRDs is assumed.

## What you will see

1. A Kubernetes cluster with the [Zhilicon operator](../../platform/operator),
   [device plugin](../../platform/device-plugin), and
   [attestation service](../../platform/attestation) installed via Helm.
2. A [`SovereignZone`](manifests/sovereignzone.yaml) declaring
   `jurisdiction: ae`, AES-256-GCM + Kyber-1024-hybrid encryption, and an
   in-zone attestation endpoint.
3. A [`DevicePool`](manifests/devicepool.yaml) of Sentinel-1 devices bound
   to that zone.
4. A [`ZhiliconWorkload`](manifests/workload.yaml) — an ECDSA-signing batch
   job — that requires a fresh attestation proof before any inference runs.
5. Telemetry flowing through the OpenTelemetry collector into Prometheus,
   and an operator dashboard showing pool health, attestation status,
   and per-device junction temperature.
6. `zhctl` driving the full lifecycle from the command line.

## Walkthrough order

| Step | File                                           | What it does                                                               |
| ---- | ---------------------------------------------- | -------------------------------------------------------------------------- |
| 0    | [`01-prereqs.md`](01-prereqs.md)               | Install kind, kubectl, Helm, zhctl; start a 3-node kind cluster            |
| 1    | [`02-install-operator.sh`](02-install-operator.sh) | Install the operator + device plugin + attestation in `zhilicon-system` |
| 2    | [`manifests/sovereignzone.yaml`](manifests/sovereignzone.yaml) | Declare the UAE fintech zone                                           |
| 3    | [`manifests/devicepool.yaml`](manifests/devicepool.yaml) | Create the Sentinel-1 pool                                               |
| 4    | [`manifests/workload.yaml`](manifests/workload.yaml) | Submit the ECDSA-batch workload                                          |
| 5    | [`notebooks/sovereign_inference.ipynb`](notebooks/sovereign_inference.ipynb) | Jupyter notebook calling the SDK from inside the attested pod  |
| 6    | [`expected-outputs/`](expected-outputs/)       | Reference snapshots of every `kubectl` / `zhctl` invocation               |
| 7    | [`troubleshooting.md`](troubleshooting.md)     | Common failures and their fixes                                           |
| 8    | [`scripts/smoke-test.sh`](scripts/smoke-test.sh) | End-to-end smoke test, also run in CI on every PR                         |

## Quick-start (reproducible in one command)

```bash
bash scripts/smoke-test.sh
```

The smoke test is deliberately minimal: it installs the operator into a kind
cluster, applies the three manifests, waits for the workload's phase to
reach `Running`, verifies the attestation proof reference is populated, and
reports failure with a full `kubectl describe` dump if any step fails.

CI runs this script on every pull request via
[`.github/workflows/demo-smoke-test.yml`](../../.github/workflows/demo-smoke-test.yml).

## Time budget

| Phase                                           | Target time |
| ----------------------------------------------- | ----------- |
| Cluster + operator install (`02-install-operator.sh`) | 3 min       |
| Zone + pool + workload apply                     | 30 sec      |
| Attestation handshake + pod scheduling           | 1 min       |
| First ECDSA batch completes                      | 30 sec      |
| Telemetry visible in Prometheus                  | within same minute |
| **Total**                                       | **≈ 5 min** |

The 10-minute figure includes reading each step; cold-cache build of the
attestation service image adds another few minutes if you are not using
pre-built images.

## What this demo does NOT cover

- **Production-grade key management.** The attestation signing key in this
  demo is an example 32-byte key sitting in a Kubernetes Secret. A real
  deployment uses an HSM-backed key custodian (see
  [`RELIABILITY_SECURITY_SUPPLY_CHAIN.md`](../../programs/portfolio-upgrade/RELIABILITY_SECURITY_SUPPLY_CHAIN.md) §2).
- **Real Sentinel-1 silicon.** The demo runs against the device plugin's
  `static` discovery backend, which reads a JSON file describing "devices."
  On real hardware you switch to the `sysfs` backend and the udev-registered
  devices appear automatically.
- **FIPS 140-3 operational mode.** See the Sentinel-1 crypto-formal
  verification plan in
  [`programs/sentinel-1/plans/CRYPTO_FORMAL_VERIFICATION_PLAN.md`](../../programs/sentinel-1/plans/CRYPTO_FORMAL_VERIFICATION_PLAN.md).

## Next after the demo

- Swap the static device-plugin backend for `sysfs` against real hardware.
- Adapt [`manifests/sovereignzone.yaml`](manifests/sovereignzone.yaml) to
  your jurisdiction (EU, GCC, ASEAN) and policy SHA.
- Use [`zhctl attest`](../../platform/fleet-cli/README.md) from your
  operations runbook to pre-warm proofs for short-lived workloads.

# Troubleshooting

Failure modes you will hit on first run and how to fix them.

## Pods stuck in `Pending`

### Symptom

```
$ kubectl -n bank-a get pods
NAME                          READY   STATUS    RESTARTS   AGE
ecdsa-batch-0001-zhilicon     0/1     Pending   0          2m
```

`kubectl describe pod` shows:

```
  Warning  FailedScheduling  ...  0/3 nodes are available: 3 Insufficient zhilicon.io/device
```

### Fix

The device plugin is not exporting any devices — most likely `/etc/zhilicon/devices.json`
is missing inside the node. Re-run the device-seeding snippet in
[`01-prereqs.md`](01-prereqs.md) and wait 60 seconds for the next plugin
heartbeat. Then:

```bash
kubectl describe node <worker-name> | grep zhilicon.io/device
# Allocatable:
#   zhilicon.io/device:  4
```

## Workload phase stuck in `Attesting`

### Symptom

```
$ kubectl -n bank-a get zhiliconworkload
NAME                POOL           PHASE       DEVICES   AGE
ecdsa-batch-0001    sentinel-uae   Attesting   0         5m
```

### Cause

The operator is waiting for an attestation sidecar to write a proof
reference onto the workload. In the demo's lightweight path this happens
through an operator-internal handshake; a stuck state usually means the
attestation service is unreachable or its SovereignZone was never resolved.

### Diagnose

```bash
kubectl -n zhilicon-system logs deploy/zhilicon-zhilicon-operator | grep -i attest
kubectl get sovereignzone uae-fintech -o jsonpath='{.status.conditions}' | jq
```

Look for the `AttestationEndpointReachable` condition. If `False` with
`ProbeFailed`, the attestation Service is not reachable from the operator's
pod. Check:

```bash
kubectl -n zhilicon-system get svc
kubectl -n zhilicon-system logs deploy/zhilicon-zhilicon-operator-attestation
```

## `SovereignZone` shows `SpecValid = False`

### Symptom

```
$ kubectl get sovereignzone uae-fintech -o yaml | yq '.status.conditions'
- type:    SpecValid
  status:  False
  reason:  ValidationFailed
  message: attestationEndpoint must be an https URL
```

### Fix

The `attestationEndpoint` must use `https://`. Apply the provided
[`manifests/sovereignzone.yaml`](manifests/sovereignzone.yaml) as-is (it
uses the in-cluster Service DNS name); do not hand-edit to `http://` for
"testing."

## `helm install` fails with `attestation.jurisdiction required`

### Symptom

```
Error: execution error at (zhilicon-operator/templates/_helpers.tpl:...): attestation.enabled=true but jurisdiction is empty
```

### Fix

The attestation sub-chart requires `jurisdiction`, `keyCustodian`,
`policySha256`, `signingKeySecretRef`, and `authorityPubkeySecretRef` when
enabled. The installer script sets all five; if you ran `helm install`
manually, compare your flags against
[`02-install-operator.sh`](02-install-operator.sh).

## `zhctl attest zone-info` returns 404

### Symptom

```
HTTPStatusError: 404 Not Found
```

### Fix

You probably pointed `zhctl` at the operator Service instead of the
attestation Service. The correct default is
`https://zhilicon-zhilicon-operator-attestation.zhilicon-system.svc.cluster.local:8443`.
From inside a pod, resolve it through `kubectl port-forward`:

```bash
kubectl -n zhilicon-system port-forward svc/zhilicon-zhilicon-operator-attestation 8443:8443 &
zhctl --attestation-endpoint https://localhost:8443 attest zone-info
```

## Collecting a diagnostic bundle

When none of the above fits, run:

```bash
bash scripts/smoke-test.sh --collect-diagnostics /tmp/zhilicon-demo-bundle
```

The bundle contains every relevant `kubectl describe`, pod logs, operator
logs, and a rendered `helm get manifest`. Attach it to a GitHub issue
filed via the
[Silicon Issue template](../../.github/ISSUE_TEMPLATE/silicon_issue.yml).

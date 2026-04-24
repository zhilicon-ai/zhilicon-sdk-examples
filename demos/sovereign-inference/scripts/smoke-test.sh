#!/usr/bin/env bash
# End-to-end smoke test for the sovereign-inference demo. Invoked by CI on
# every pull request via .github/workflows/demo-smoke-test.yml, and safe to
# run locally.
#
# Exits 0 on success. On failure, prints kubectl / helm diagnostic output
# and exits non-zero.

set -euo pipefail

CTX=${KUBE_CONTEXT:-kind-zhilicon-demo}
NS_SYS=${NS_SYS:-zhilicon-system}
NS_APP=${NS_APP:-bank-a}
TIMEOUT=${TIMEOUT:-5m}
MANIFEST_DIR=${MANIFEST_DIR:-demo/sovereign-inference/manifests}
COLLECT_BUNDLE=""

banner() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail()   { printf '\n\033[1;31mFAIL: %s\033[0m\n' "$*" >&2; collect_diagnostics; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --collect-diagnostics)
      COLLECT_BUNDLE="/tmp/zhilicon-demo-bundle-$(date +%s)"
      ;;
    --collect-diagnostics=*)
      COLLECT_BUNDLE="${arg#*=}"
      ;;
    *)
      printf 'unknown argument: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

collect_diagnostics() {
  [ -z "$COLLECT_BUNDLE" ] && return
  mkdir -p "$COLLECT_BUNDLE"
  banner "Collecting diagnostics into $COLLECT_BUNDLE"
  kubectl --context "$CTX" -n "$NS_SYS" get all -o wide > "$COLLECT_BUNDLE/system-all.txt" 2>&1 || true
  kubectl --context "$CTX" -n "$NS_APP" get all -o wide > "$COLLECT_BUNDLE/app-all.txt" 2>&1 || true
  kubectl --context "$CTX" get sovereignzone  -o yaml > "$COLLECT_BUNDLE/zones.yaml"    2>&1 || true
  kubectl --context "$CTX" get devicepool     -o yaml > "$COLLECT_BUNDLE/pools.yaml"    2>&1 || true
  kubectl --context "$CTX" -n "$NS_APP" get zhiliconworkload -o yaml \
                                                     > "$COLLECT_BUNDLE/workloads.yaml" 2>&1 || true
  kubectl --context "$CTX" -n "$NS_SYS" logs deploy/zhilicon-zhilicon-operator --all-containers --tail=1000 \
                                                     > "$COLLECT_BUNDLE/operator.log"  2>&1 || true
  helm    --kube-context "$CTX" -n "$NS_SYS" get manifest zhilicon \
                                                     > "$COLLECT_BUNDLE/helm-manifest.yaml" 2>&1 || true
  printf 'Diagnostics captured at %s\n' "$COLLECT_BUNDLE"
}

# ------------------------------------------------------------------------------
# 1. Sanity
# ------------------------------------------------------------------------------

banner "Preflight"
kubectl --context "$CTX" version --short >/dev/null || fail "cluster not reachable"
command -v helm   >/dev/null             || fail "helm not installed"
command -v jq     >/dev/null             || fail "jq not installed"

# ------------------------------------------------------------------------------
# 2. Apply the three demo manifests in order
# ------------------------------------------------------------------------------

banner "Apply Namespace + SovereignZone"
kubectl --context "$CTX" apply -f "$MANIFEST_DIR/namespace.yaml"
kubectl --context "$CTX" apply -f "$MANIFEST_DIR/sovereignzone.yaml"

banner "Wait for SovereignZone.SpecValid=True"
for i in $(seq 1 60); do
  s=$(kubectl --context "$CTX" get sovereignzone uae-fintech \
        -o jsonpath='{.status.conditions[?(@.type=="SpecValid")].status}' 2>/dev/null || true)
  if [ "$s" = "True" ]; then break; fi
  sleep 2
done
[ "$s" = "True" ] || fail "SovereignZone did not reach SpecValid=True"

banner "Apply DevicePool"
kubectl --context "$CTX" apply -f "$MANIFEST_DIR/devicepool.yaml"

banner "Wait for DevicePool.Eligible=True"
for i in $(seq 1 60); do
  s=$(kubectl --context "$CTX" get devicepool sentinel-uae \
        -o jsonpath='{.status.conditions[?(@.type=="Eligible")].status}' 2>/dev/null || true)
  if [ "$s" = "True" ]; then break; fi
  sleep 2
done
[ "$s" = "True" ] || fail "DevicePool did not reach Eligible=True"

banner "Apply ZhiliconWorkload"
kubectl --context "$CTX" apply -f "$MANIFEST_DIR/workload.yaml"

banner "Wait for ZhiliconWorkload phase in {Running,Succeeded}"
for i in $(seq 1 150); do
  phase=$(kubectl --context "$CTX" -n "$NS_APP" get zhiliconworkload ecdsa-batch-0001 \
            -o jsonpath='{.status.phase}' 2>/dev/null || true)
  if [ "$phase" = "Running" ] || [ "$phase" = "Succeeded" ]; then break; fi
  sleep 2
done
case "$phase" in
  Running|Succeeded) ;;
  *) fail "workload phase=$phase (expected Running or Succeeded)" ;;
esac

banner "Verify the managed Pod is alive and attested"
pod=$(kubectl --context "$CTX" -n "$NS_APP" get pod -l "zhilicon.io/workload=ecdsa-batch-0001" \
        -o jsonpath='{.items[0].metadata.name}')
[ -n "$pod" ] || fail "managed Pod not found"
env=$(kubectl --context "$CTX" -n "$NS_APP" exec "$pod" -- env 2>/dev/null || true)
echo "$env" | grep -q 'ZHILICON_SOVEREIGN_ZONE=uae-fintech' \
  || fail "ZHILICON_SOVEREIGN_ZONE env var not injected"
echo "$env" | grep -q 'ZHILICON_JURISDICTION=ae' \
  || fail "ZHILICON_JURISDICTION env var not injected"

banner "PASS"
kubectl --context "$CTX" -n "$NS_APP" get zhiliconworkload
exit 0

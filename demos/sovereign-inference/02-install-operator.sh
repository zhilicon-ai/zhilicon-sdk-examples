#!/usr/bin/env bash
# Step 1 — install the Zhilicon operator stack into the demo cluster.
#
# Idempotent: safe to rerun.

set -euo pipefail

: "${KUBE_CONTEXT:=kind-zhilicon-demo}"
: "${NS:=zhilicon-system}"
: "${CHART:=platform/charts/zhilicon-operator}"
: "${OPERATOR_IMAGE:=zhilicon/operator:dev}"
: "${DEVICE_PLUGIN_IMAGE:=zhilicon/device-plugin:dev}"
: "${ATTESTATION_IMAGE:=zhilicon/attestation:dev}"

banner() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

banner "Target context: ${KUBE_CONTEXT}"
kubectl --context "${KUBE_CONTEXT}" version --short >/dev/null

banner "Build + load images into kind"
docker build -t "${OPERATOR_IMAGE}"        platform/operator
docker build -t "${DEVICE_PLUGIN_IMAGE}"   platform/device-plugin
docker build -t "${ATTESTATION_IMAGE}"     platform/attestation
kind load docker-image "${OPERATOR_IMAGE}"        --name "${KUBE_CONTEXT#kind-}"
kind load docker-image "${DEVICE_PLUGIN_IMAGE}"   --name "${KUBE_CONTEXT#kind-}"
kind load docker-image "${ATTESTATION_IMAGE}"     --name "${KUBE_CONTEXT#kind-}"

banner "Create attestation Secrets (example keys — not for production)"
kubectl --context "${KUBE_CONTEXT}" get ns "${NS}" >/dev/null 2>&1 \
  || kubectl --context "${KUBE_CONTEXT}" create namespace "${NS}"
# 32-byte demo signing key + matching authority public key (base64 of
# all-zeros for illustration; a production deployment uses HSM-provisioned
# keys — see RELIABILITY_SECURITY_SUPPLY_CHAIN.md §2).
DEMO_KEY_B64="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
DEMO_PUB_B64="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
kubectl --context "${KUBE_CONTEXT}" -n "${NS}" \
    create secret generic signing-secret \
    --from-literal=signing_key_b64="${DEMO_KEY_B64}" \
    --dry-run=client -o yaml | kubectl --context "${KUBE_CONTEXT}" apply -f -
kubectl --context "${KUBE_CONTEXT}" -n "${NS}" \
    create secret generic authority-secret \
    --from-literal=authority_pubkey_b64="${DEMO_PUB_B64}" \
    --dry-run=client -o yaml | kubectl --context "${KUBE_CONTEXT}" apply -f -

banner "Helm install"
helm --kube-context "${KUBE_CONTEXT}" upgrade --install zhilicon "${CHART}" \
    --namespace "${NS}" \
    --create-namespace \
    --set operator.image.tag=dev \
    --set devicePlugin.image.tag=dev \
    --set devicePlugin.discoveryBackend=static \
    --set attestation.enabled=true \
    --set attestation.image.tag=dev \
    --set attestation.jurisdiction=ae \
    --set attestation.keyCustodian=uae-cba-ca \
    --set attestation.policySha256=00000000000000000000000000000000000000000000000000000000000000 \
    --set attestation.signingKeySecretRef=signing-secret \
    --set attestation.authorityPubkeySecretRef=authority-secret \
    --wait --timeout=5m

banner "Wait for operator + device plugin rollouts"
kubectl --context "${KUBE_CONTEXT}" -n "${NS}" rollout status deploy/zhilicon-zhilicon-operator
kubectl --context "${KUBE_CONTEXT}" -n "${NS}" rollout status daemonset/zhilicon-zhilicon-operator-device-plugin

banner "Installed"
kubectl --context "${KUBE_CONTEXT}" -n "${NS}" get all

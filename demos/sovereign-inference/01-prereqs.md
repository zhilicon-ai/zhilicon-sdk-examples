# Step 0 — Prerequisites

Install the following and confirm versions before continuing.

| Tool        | Minimum | Check                            |
| ----------- | ------- | -------------------------------- |
| `docker`    | 24.x    | `docker version`                 |
| `kubectl`   | 1.28    | `kubectl version --client`       |
| `kind`      | 0.22    | `kind version`                   |
| `helm`      | 3.15    | `helm version --short`           |
| `python`    | 3.11    | `python --version`               |
| `jq`        | 1.6+    | `jq --version`                   |

## Install `zhctl`

```bash
pip install --editable 'platform/fleet-cli[dev]'
zhctl --version
```

## Start a kind cluster

```bash
cat <<'EOF' > /tmp/zhilicon-demo-kind.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
    labels:
      zhilicon.io/chip-family: sentinel-1
      zhilicon.io/region: ae
  - role: worker
    labels:
      zhilicon.io/chip-family: sentinel-1
      zhilicon.io/region: ae
EOF

kind create cluster --name zhilicon-demo --config /tmp/zhilicon-demo-kind.yaml
kubectl cluster-info --context kind-zhilicon-demo
```

Two worker nodes carry the `zhilicon.io/chip-family=sentinel-1` label so the
device plugin's DaemonSet lands on them. The control plane is left un-labelled
and stays workload-free.

## Seed the simulated device list

The device plugin's `static` backend reads `/etc/zhilicon/devices.json` on
each node. Create that file inside each worker via kind's node-shell:

```bash
for node in zhilicon-demo-worker zhilicon-demo-worker2; do
  docker exec "$node" bash -c 'mkdir -p /etc/zhilicon && cat > /etc/zhilicon/devices.json' <<'DEV_EOF'
{
  "devices": [
    { "ID": "zhi0", "ChipFamily": "sentinel-1", "NUMANode": 0, "Healthy": true },
    { "ID": "zhi1", "ChipFamily": "sentinel-1", "NUMANode": 0, "Healthy": true },
    { "ID": "zhi2", "ChipFamily": "sentinel-1", "NUMANode": 1, "Healthy": true },
    { "ID": "zhi3", "ChipFamily": "sentinel-1", "NUMANode": 1, "Healthy": true }
  ]
}
DEV_EOF
done
```

Each worker now reports four Sentinel-1 devices — eight total, enough for the
demo workload which requests four.

## Sanity-check

```bash
kubectl get nodes -o wide
kubectl get nodes -l zhilicon.io/chip-family=sentinel-1
```

You should see the two `zhilicon-demo-worker*` nodes in the second listing.

Proceed to [`02-install-operator.sh`](02-install-operator.sh).

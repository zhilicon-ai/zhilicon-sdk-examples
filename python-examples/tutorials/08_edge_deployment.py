#!/usr/bin/env python3
"""
Zhilicon Tutorial 08 -- Edge Deployment
=========================================

Edge deployment tutorial across Zhilicon's hardware portfolio:
  1. Medical edge (Discovery-1 in hospital)
  2. Space edge (Horizon-1 on satellite)
  3. Telecom edge (Nexus-1 in base station)
  4. OTA model updates
  5. Power management
  6. Telemetry and monitoring

How to run:
    pip install zhilicon
    python 08_edge_deployment.py

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys, time, random, hashlib, json, uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ── Simulation layer ────────────────────────────────────────────────────

@dataclass
class EdgeDeviceStatus:
    device_id: str = ""
    chip_type: str = ""
    temperature_c: float = 0.0
    power_watts: float = 0.0
    memory_used_pct: float = 0.0
    uptime_hours: float = 0.0
    models_loaded: int = 0
    inferences_total: int = 0

class MedicalEdgeNode:
    def __init__(self, hospital_id: str, device_id: str = "disc-001"):
        self.hospital_id = hospital_id
        self.device_id = device_id
        self.chip = "Discovery-1"
        self.models: List[str] = []

    def deploy_model(self, model_name: str, version: str) -> Dict:
        self.models.append(model_name)
        return {"model": model_name, "version": version, "status": "deployed",
                "device": self.device_id, "hipaa_compliant": True}

    def get_status(self) -> EdgeDeviceStatus:
        return EdgeDeviceStatus(
            device_id=self.device_id, chip_type=self.chip,
            temperature_c=random.uniform(45, 65), power_watts=random.uniform(25, 45),
            memory_used_pct=random.uniform(40, 75), uptime_hours=random.uniform(100, 5000),
            models_loaded=len(self.models), inferences_total=random.randint(10000, 500000))

class SpaceEdgeNode:
    def __init__(self, satellite_id: str, device_id: str = "hor-001"):
        self.satellite_id = satellite_id
        self.device_id = device_id
        self.chip = "Horizon-1"
        self.orbit_altitude_km = 550
        self.in_eclipse = False

    def deploy_model(self, model_name: str, compressed: bool = True) -> Dict:
        return {"model": model_name, "compressed": compressed,
                "uplink_size_mb": random.uniform(5, 20),
                "status": "queued_for_next_pass"}

    def get_status(self) -> EdgeDeviceStatus:
        return EdgeDeviceStatus(
            device_id=self.device_id, chip_type=self.chip,
            temperature_c=random.uniform(-20, 45), power_watts=random.uniform(8, 15),
            memory_used_pct=random.uniform(30, 60), uptime_hours=random.uniform(1000, 20000),
            models_loaded=2, inferences_total=random.randint(1000, 50000))

class TelecomEdgeNode:
    def __init__(self, bs_id: str, device_id: str = "nex-001"):
        self.bs_id = bs_id
        self.device_id = device_id
        self.chip = "Nexus-1"

    def deploy_model(self, model_name: str) -> Dict:
        return {"model": model_name, "status": "deployed",
                "latency_requirement_ms": 1.0, "o_ran_compatible": True}

    def get_status(self) -> EdgeDeviceStatus:
        return EdgeDeviceStatus(
            device_id=self.device_id, chip_type=self.chip,
            temperature_c=random.uniform(50, 80), power_watts=random.uniform(40, 75),
            memory_used_pct=random.uniform(50, 85), uptime_hours=random.uniform(500, 10000),
            models_loaded=3, inferences_total=random.randint(1000000, 50000000))

class OTAUpdateManager:
    def __init__(self):
        self.updates: List[Dict] = []

    def create_update(self, model_name: str, version: str,
                      target_devices: List[str]) -> Dict:
        update_id = uuid.uuid4().hex[:12]
        update = {"update_id": update_id, "model": model_name, "version": version,
                  "targets": target_devices, "status": "staged",
                  "size_mb": random.uniform(10, 500),
                  "rollback_version": f"v{float(version[1:])-0.1:.1f}"}
        self.updates.append(update)
        return update

    def deploy_update(self, update_id: str, strategy: str = "canary") -> Dict:
        return {"update_id": update_id, "strategy": strategy,
                "rollout_pct": 10 if strategy == "canary" else 100,
                "status": "deploying", "estimated_time_min": random.randint(5, 30)}

class PowerManager:
    def __init__(self, device_type: str):
        self.device_type = device_type
        self.modes = {"full": 1.0, "balanced": 0.7, "eco": 0.4, "sleep": 0.05}

    def set_mode(self, mode: str) -> Dict:
        factor = self.modes.get(mode, 1.0)
        base_power = {"Discovery-1": 45, "Horizon-1": 15, "Nexus-1": 75}.get(self.device_type, 50)
        return {"mode": mode, "power_watts": base_power * factor,
                "compute_available_pct": factor * 100,
                "estimated_battery_hours": random.uniform(2, 48) / factor if factor > 0 else float("inf")}

class TelemetryCollector:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.metrics: List[Dict] = []

    def collect(self) -> Dict:
        m = {"device_id": self.device_id, "timestamp": time.time(),
             "temperature_c": random.uniform(40, 80),
             "power_watts": random.uniform(10, 80),
             "memory_used_pct": random.uniform(30, 90),
             "inference_latency_ms": random.uniform(0.5, 50),
             "throughput_inferences_per_sec": random.randint(10, 10000),
             "errors": random.randint(0, 2),
             "seu_corrections": random.randint(0, 5)}
        self.metrics.append(m)
        return m

# ── Tutorial ────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}\n")

def tutorial_medical_edge():
    section("1. Medical Edge (Discovery-1 in Hospital)")
    node = MedicalEdgeNode("Al Mafraq Hospital", "disc-amh-001")
    result = node.deploy_model("medical-ct-seg-v3", "v3.2")
    print(f"Hospital: {node.hospital_id}")
    print(f"Deployed: {result['model']} v{result['version']}")
    print(f"HIPAA compliant: {result['hipaa_compliant']}")
    status = node.get_status()
    print(f"\nDevice Status:")
    print(f"  Chip        : {status.chip_type}")
    print(f"  Temperature : {status.temperature_c:.1f} C")
    print(f"  Power       : {status.power_watts:.1f} W")
    print(f"  Memory used : {status.memory_used_pct:.1f}%")
    print(f"  Uptime      : {status.uptime_hours:.0f} hours")
    print(f"  Inferences  : {status.inferences_total:,}")

def tutorial_space_edge():
    section("2. Space Edge (Horizon-1 on Satellite)")
    node = SpaceEdgeNode("SAT-ZH-042", "hor-042-001")
    result = node.deploy_model("earth-obs-seg-v3", compressed=True)
    print(f"Satellite: {node.satellite_id} (LEO, {node.orbit_altitude_km}km)")
    print(f"Model upload: {result['model']}")
    print(f"  Compressed: {result['compressed']}")
    print(f"  Uplink size: {result['uplink_size_mb']:.1f} MB")
    print(f"  Status: {result['status']}")
    status = node.get_status()
    print(f"\nDevice Status:")
    print(f"  Temperature : {status.temperature_c:.1f} C (orbital thermal)")
    print(f"  Power       : {status.power_watts:.1f} W (solar budget)")
    print(f"  Uptime      : {status.uptime_hours:.0f} hours in orbit")

def tutorial_telecom_edge():
    section("3. Telecom Edge (Nexus-1 in Base Station)")
    node = TelecomEdgeNode("BS-DXB-042", "nex-dxb-001")
    result = node.deploy_model("beamforming-ai-v2")
    print(f"Base Station: {node.bs_id}")
    print(f"Deployed: {result['model']}")
    print(f"  Latency req : {result['latency_requirement_ms']} ms")
    print(f"  O-RAN compat: {result['o_ran_compatible']}")
    status = node.get_status()
    print(f"\nDevice Status:")
    print(f"  Inferences  : {status.inferences_total:,} (beam updates)")

def tutorial_ota_updates():
    section("4. OTA Model Updates")
    ota = OTAUpdateManager()
    update = ota.create_update("medical-ct-seg-v3", "v3.3",
                                ["disc-amh-001", "disc-skmc-001", "disc-ccad-001"])
    print(f"Update created:")
    print(f"  ID: {update['update_id']}")
    print(f"  Model: {update['model']} -> {update['version']}")
    print(f"  Targets: {len(update['targets'])} devices")
    print(f"  Size: {update['size_mb']:.1f} MB")
    print(f"  Rollback: {update['rollback_version']}")
    deploy = ota.deploy_update(update["update_id"], strategy="canary")
    print(f"\nDeployment:")
    print(f"  Strategy: {deploy['strategy']} ({deploy['rollout_pct']}% initially)")
    print(f"  Status: {deploy['status']}")
    print(f"  ETA: {deploy['estimated_time_min']} minutes")

def tutorial_power_management():
    section("5. Power Management")
    for device_type in ["Discovery-1", "Horizon-1", "Nexus-1"]:
        pm = PowerManager(device_type)
        print(f"\n{device_type}:")
        for mode in ["full", "balanced", "eco", "sleep"]:
            r = pm.set_mode(mode)
            print(f"  {mode:10s}: {r['power_watts']:5.1f}W | "
                  f"Compute: {r['compute_available_pct']:5.1f}%")

def tutorial_telemetry():
    section("6. Telemetry and Monitoring")
    collector = TelemetryCollector("disc-amh-001")
    print(f"Collecting telemetry from {collector.device_id}:\n")
    print(f"  {'Time':>10} {'Temp(C)':>8} {'Power(W)':>9} {'Mem%':>6} "
          f"{'Lat(ms)':>8} {'Thru/s':>8} {'Errors':>7}")
    for i in range(8):
        m = collector.collect()
        ts = time.strftime("%H:%M:%S", time.localtime(m["timestamp"]))
        print(f"  {ts:>10} {m['temperature_c']:>7.1f} {m['power_watts']:>8.1f} "
              f"{m['memory_used_pct']:>5.1f} {m['inference_latency_ms']:>7.1f} "
              f"{m['throughput_inferences_per_sec']:>7} {m['errors']:>6}")
        time.sleep(0.05)
    print(f"\nCollected {len(collector.metrics)} telemetry points.")

def main():
    print("=" * 60)
    print("  Zhilicon Tutorial 08: Edge Deployment")
    print("=" * 60)
    tutorial_medical_edge()
    tutorial_space_edge()
    tutorial_telecom_edge()
    tutorial_ota_updates()
    tutorial_power_management()
    tutorial_telemetry()
    print(f"\nTutorial complete! Next: 09_compliance.py")

if __name__ == "__main__":
    main()

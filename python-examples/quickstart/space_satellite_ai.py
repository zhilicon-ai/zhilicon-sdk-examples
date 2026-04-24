#!/usr/bin/env python3
"""
Zhilicon Quickstart -- Space Satellite AI Perception
=====================================================

Set up on-orbit AI perception on Horizon-1 for real-time Earth observation.
Horizon-1 is radiation-hardened (TMR + ECC) and runs in LEO conditions.

This example shows:
  - Initialize a Horizon-1 device with space constraints
  - Load a satellite imagery segmentation model
  - Run on-orbit inference (cloud detection, land classification)
  - Handle eclipse scheduling and power constraints

How to run:
    pip install zhilicon
    python space_satellite_ai.py

Expected output:
    === On-Orbit AI Perception (Horizon-1) ===
    Satellite   : SAT-ZH-042 (LEO, 550km altitude)
    Hardware    : Horizon-1 (rad-hardened, TMR enabled)
    Power budget: 15W (solar panel illuminated)
    --------------------------------------------------
    Loading model: zhilicon/earth-obs-seg-v3 (quantized INT8)
    Model loaded: 12.4 MB, optimized for 15W power envelope
    Processing swath image (4096x4096 pixels, 4 bands) ...
    --------------------------------------------------
    Classification Results:
      Cloud cover : 23.4%
      Water       : 31.2%
      Vegetation  : 28.7%
      Urban       : 11.3%
      Bare soil   : 5.4%
    Anomaly detected: Wildfire hotspot at (lat: 34.12, lon: -118.44)
    --------------------------------------------------
    Telemetry downlinked: 2.4 KB compressed metadata
    Full image stored on-board for next ground pass

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys
import time
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ── Simulation layer ────────────────────────────────────────────────────

@dataclass
class OrbitalParams:
    """Satellite orbital parameters."""
    altitude_km: float = 550.0
    inclination_deg: float = 97.4   # Sun-synchronous
    period_min: float = 95.6
    in_eclipse: bool = False
    lat: float = 34.12
    lon: float = -118.44

@dataclass
class PowerBudget:
    """Power budget for on-orbit processing."""
    total_watts: float = 15.0
    ai_allocation_watts: float = 12.0
    solar_illuminated: bool = True
    battery_soc_percent: float = 87.3

@dataclass
class SwathImage:
    """Simulated satellite swath image."""
    width: int = 4096
    height: int = 4096
    bands: int = 4  # R, G, B, NIR
    gsd_meters: float = 3.0  # Ground sample distance
    center_lat: float = 34.12
    center_lon: float = -118.44

@dataclass
class ClassificationResult:
    """Land cover classification result."""
    classes: Dict[str, float] = field(default_factory=lambda: {
        "cloud": 23.4, "water": 31.2, "vegetation": 28.7,
        "urban": 11.3, "bare_soil": 5.4,
    })
    anomalies: List[Dict[str, Any]] = field(default_factory=lambda: [{
        "type": "wildfire_hotspot",
        "lat": 34.12, "lon": -118.44,
        "confidence": 0.91,
        "estimated_area_km2": 2.3,
    }])
    inference_time_ms: float = 340.0
    power_consumed_wh: float = 0.0014

class Horizon1Device:
    """Simulated Horizon-1 space AI processor."""
    def __init__(self, satellite_id: str = "SAT-ZH-042"):
        self.satellite_id = satellite_id
        self.orbital = OrbitalParams()
        self.power = PowerBudget()
        self.tmr_enabled = True
        self.rad_hardened = True
        self.seu_corrections = 0

    def load_model(self, model_name: str, quantize: str = "int8") -> Dict[str, Any]:
        """Load a model optimized for on-orbit execution."""
        time.sleep(0.1)
        return {
            "name": model_name,
            "size_mb": 12.4,
            "quantization": quantize,
            "power_envelope_watts": self.power.ai_allocation_watts,
        }

    def process_swath(self, image: SwathImage) -> ClassificationResult:
        """Run on-orbit inference on a swath image."""
        time.sleep(0.2)
        return ClassificationResult(
            power_consumed_wh=random.uniform(0.001, 0.002),
        )

    def downlink_metadata(self, result: ClassificationResult) -> Dict[str, Any]:
        """Compress and prepare metadata for downlink."""
        metadata_size = 2400  # bytes
        return {
            "size_bytes": metadata_size,
            "compressed": True,
            "anomalies_flagged": len(result.anomalies),
        }

# ── THE ACTUAL EXAMPLE ──────────────────────────────────────────────────

def main():
    """On-orbit AI perception on Horizon-1."""
    print("=== On-Orbit AI Perception (Horizon-1) ===\n")

    # Step 1: Initialize Horizon-1 device
    device = Horizon1Device(satellite_id="SAT-ZH-042")
    print(f"Satellite   : {device.satellite_id} (LEO, {device.orbital.altitude_km:.0f}km altitude)")
    print(f"Hardware    : Horizon-1 (rad-hardened, TMR {'enabled' if device.tmr_enabled else 'disabled'})")
    solar_status = "solar panel illuminated" if device.power.solar_illuminated else "IN ECLIPSE"
    print(f"Power budget: {device.power.total_watts}W ({solar_status})")
    print("-" * 50)

    # Step 2: Load the Earth observation model (INT8 quantized for low power)
    model_name = "zhilicon/earth-obs-seg-v3"
    print(f"Loading model: {model_name} (quantized INT8)")
    model_info = device.load_model(model_name, quantize="int8")
    print(f"Model loaded: {model_info['size_mb']} MB, optimized for "
          f"{model_info['power_envelope_watts']}W power envelope")

    # Step 3: Process a swath image
    image = SwathImage()
    print(f"Processing swath image ({image.width}x{image.height} pixels, "
          f"{image.bands} bands) ...")
    result = device.process_swath(image)

    # Step 4: Print classification results
    print("-" * 50)
    print("Classification Results:")
    for cls_name, pct in result.classes.items():
        label = cls_name.replace("_", " ").title()
        print(f"  {label:12s}: {pct:.1f}%")

    # Step 5: Report anomalies
    for anomaly in result.anomalies:
        print(f"Anomaly detected: {anomaly['type'].replace('_', ' ').title()} "
              f"at (lat: {anomaly['lat']}, lon: {anomaly['lon']})")

    # Step 6: Prepare downlink
    print("-" * 50)
    dl = device.downlink_metadata(result)
    print(f"Telemetry downlinked: {dl['size_bytes'] / 1024:.1f} KB compressed metadata")
    print("Full image stored on-board for next ground pass")
    print(f"\nSEU corrections this orbit: {device.seu_corrections}")

if __name__ == "__main__":
    main()

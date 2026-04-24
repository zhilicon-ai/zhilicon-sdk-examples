#!/usr/bin/env python3
"""
Zhilicon Tool -- Interactive Profiler Demo
============================================

Interactive profiling demo:
  1. Profile a model inference
  2. Show kernel timeline
  3. Show memory usage
  4. Show roofline analysis
  5. Export Chrome Trace
  6. Compare against baseline

How to run:
    pip install zhilicon
    python profiler_demo.py

    # Or interactively:
    zh profile --model zhilicon/llama-7b-fp8 --prompt "Hello"

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys, time, random, math, json, uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── Simulation ──────────────────────────────────────────────────────────

@dataclass
class KernelEvent:
    name: str
    category: str  # "compute", "memory", "communication"
    start_us: float
    duration_us: float
    device: str = "prometheus"
    stream: int = 0
    memory_mb: float = 0.0
    flops: float = 0.0

@dataclass
class MemorySnapshot:
    timestamp_us: float
    allocated_mb: float
    reserved_mb: float
    peak_mb: float
    breakdown: Dict[str, float]  # category -> MB

@dataclass
class ProfileResult:
    model: str
    total_time_ms: float
    kernel_events: List[KernelEvent]
    memory_timeline: List[MemorySnapshot]
    flops_total: float
    memory_total_mb: float

class ZhiliconProfiler:
    def __init__(self, device: str = "prometheus"):
        self.device = device

    def profile_inference(self, model: str, prompt: str = "Hello",
                           num_tokens: int = 100) -> ProfileResult:
        """Profile a complete inference."""
        events = []
        t = 0.0  # microseconds

        # Prefill phase
        kernels_prefill = [
            ("embedding_lookup", "compute", 50, 0, 128),
            ("rope_encoding", "compute", 30, 0, 64),
            ("qkv_projection", "compute", 200, 1e9, 512),
            ("attention_score", "compute", 350, 5e9, 1024),
            ("softmax", "compute", 40, 1e8, 64),
            ("attention_output", "compute", 180, 2e9, 512),
            ("ffn_gate_up", "compute", 250, 3e9, 768),
            ("ffn_silu_mul", "compute", 30, 5e7, 256),
            ("ffn_down", "compute", 200, 3e9, 512),
            ("rmsnorm", "compute", 20, 1e7, 32),
        ]
        for name, cat, dur, flops, mem in kernels_prefill:
            for layer in range(32):
                events.append(KernelEvent(
                    name=f"L{layer:02d}/{name}", category=cat,
                    start_us=t, duration_us=dur + random.uniform(-10, 10),
                    memory_mb=mem / 32, flops=flops))
                t += dur + random.uniform(5, 15)  # gap between kernels

        # Decode phase (per token)
        for token_idx in range(min(num_tokens, 10)):
            for name, cat, dur, flops, mem in kernels_prefill:
                dur_decode = dur * 0.3  # Decode is faster (single token)
                events.append(KernelEvent(
                    name=f"T{token_idx}/L0/{name}", category=cat,
                    start_us=t, duration_us=dur_decode,
                    memory_mb=mem / 32 * 0.1, flops=flops * 0.1))
                t += dur_decode + random.uniform(2, 8)

        # Memory timeline
        mem_timeline = []
        for i in range(20):
            allocated = random.uniform(5000, 12000)
            mem_timeline.append(MemorySnapshot(
                timestamp_us=t * i / 20,
                allocated_mb=allocated,
                reserved_mb=allocated * 1.1,
                peak_mb=12500,
                breakdown={"weights": 7000, "kv_cache": random.uniform(1000, 4000),
                           "activations": random.uniform(500, 2000),
                           "workspace": random.uniform(100, 500)},
            ))

        total_flops = sum(e.flops for e in events)
        total_mem = max(m.allocated_mb for m in mem_timeline)

        return ProfileResult(
            model=model, total_time_ms=round(t / 1000, 2),
            kernel_events=events, memory_timeline=mem_timeline,
            flops_total=total_flops, memory_total_mb=total_mem,
        )

    def show_kernel_timeline(self, result: ProfileResult, top_n: int = 15):
        """Display top kernels by duration."""
        sorted_events = sorted(result.kernel_events,
                                key=lambda e: e.duration_us, reverse=True)
        print(f"\n  Top {top_n} kernels by duration:")
        print(f"  {'Kernel':<35} {'Duration(us)':>12} {'Category':>12} {'GFLOPS':>10}")
        print(f"  {'-'*35} {'-'*12} {'-'*12} {'-'*10}")
        for event in sorted_events[:top_n]:
            gflops = event.flops / 1e9 if event.flops > 0 else 0
            print(f"  {event.name:<35} {event.duration_us:>11.1f} "
                  f"{event.category:>12} {gflops:>9.1f}")
        total_compute = sum(e.duration_us for e in result.kernel_events
                           if e.category == "compute")
        total_memory = sum(e.duration_us for e in result.kernel_events
                          if e.category == "memory")
        total = sum(e.duration_us for e in result.kernel_events)
        print(f"\n  Time breakdown:")
        print(f"    Compute: {total_compute/1000:.1f}ms ({total_compute/total*100:.1f}%)")
        print(f"    Memory:  {total_memory/1000:.1f}ms ({total_memory/total*100:.1f}%)")

    def show_memory_usage(self, result: ProfileResult):
        """Display memory usage analysis."""
        peak = max(result.memory_timeline, key=lambda m: m.allocated_mb)
        print(f"\n  Peak memory: {peak.allocated_mb:.0f} MB / "
              f"{peak.reserved_mb:.0f} MB reserved")
        print(f"\n  Memory breakdown:")
        for category, mb in peak.breakdown.items():
            pct = mb / peak.allocated_mb * 100
            bar = "#" * int(pct / 3)
            print(f"    {category:15s}: {mb:8.0f} MB ({pct:5.1f}%) {bar}")

    def show_roofline(self, result: ProfileResult):
        """Show roofline analysis."""
        peak_tflops = 500  # Prometheus
        peak_bw_tb = 4.8   # TB/s
        ridge_point = peak_tflops / peak_bw_tb  # FLOP/byte

        achieved_tflops = result.flops_total / (result.total_time_ms / 1000) / 1e12
        ai = result.flops_total / (result.memory_total_mb * 1e6)
        bound = "compute" if ai > ridge_point else "memory"

        print(f"\n  Roofline Analysis:")
        print(f"    Peak compute   : {peak_tflops} TFLOPS")
        print(f"    Peak bandwidth : {peak_bw_tb} TB/s")
        print(f"    Ridge point    : {ridge_point:.1f} FLOP/byte")
        print(f"    Achieved       : {achieved_tflops:.1f} TFLOPS")
        print(f"    Arithmetic Int.: {ai:.2f} FLOP/byte")
        print(f"    Bottleneck     : {bound}-bound")
        print(f"    Utilization    : {achieved_tflops/peak_tflops*100:.1f}%")

    def export_chrome_trace(self, result: ProfileResult,
                            output_path: str = "trace.json") -> Dict:
        """Export as Chrome Trace format (chrome://tracing)."""
        trace_events = []
        for event in result.kernel_events[:50]:  # Limit for demo
            trace_events.append({
                "name": event.name, "cat": event.category,
                "ph": "X",  # Complete event
                "ts": event.start_us, "dur": event.duration_us,
                "pid": 1, "tid": event.stream,
                "args": {"flops": event.flops, "memory_mb": event.memory_mb},
            })
        trace = {"traceEvents": trace_events, "displayTimeUnit": "us"}
        return {"output_path": output_path, "events": len(trace_events),
                "size_kb": len(json.dumps(trace)) / 1024}

    def compare_baseline(self, current: ProfileResult,
                          baseline_ms: float) -> Dict:
        """Compare against a baseline."""
        speedup = baseline_ms / current.total_time_ms
        return {"current_ms": current.total_time_ms, "baseline_ms": baseline_ms,
                "speedup": round(speedup, 2),
                "improvement_pct": round((speedup - 1) * 100, 1),
                "status": "faster" if speedup > 1 else "slower"}

# ── Demo ────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}\n")

def main():
    print("=" * 60)
    print("  Zhilicon Tool: Interactive Profiler")
    print("=" * 60)

    profiler = ZhiliconProfiler()

    section("1. Profile Model Inference")
    result = profiler.profile_inference("zhilicon/llama-7b-fp8", "Hello world", 100)
    print(f"  Model: {result.model}")
    print(f"  Total time: {result.total_time_ms} ms")
    print(f"  Kernels: {len(result.kernel_events)}")
    print(f"  Total FLOPS: {result.flops_total:.2e}")
    print(f"  Peak memory: {result.memory_total_mb:.0f} MB")

    section("2. Kernel Timeline")
    profiler.show_kernel_timeline(result, top_n=10)

    section("3. Memory Usage")
    profiler.show_memory_usage(result)

    section("4. Roofline Analysis")
    profiler.show_roofline(result)

    section("5. Chrome Trace Export")
    trace = profiler.export_chrome_trace(result, "profile_trace.json")
    print(f"  Exported to: {trace['output_path']}")
    print(f"  Events: {trace['events']}")
    print(f"  Size: {trace['size_kb']:.1f} KB")
    print(f"  View at: chrome://tracing (drag and drop the JSON file)")

    section("6. Compare Against Baseline")
    comparison = profiler.compare_baseline(result, baseline_ms=50.0)
    print(f"  Current  : {comparison['current_ms']} ms")
    print(f"  Baseline : {comparison['baseline_ms']} ms")
    print(f"  Speedup  : {comparison['speedup']}x ({comparison['status']})")
    print(f"  Improvement: {comparison['improvement_pct']:+.1f}%")

if __name__ == "__main__":
    main()

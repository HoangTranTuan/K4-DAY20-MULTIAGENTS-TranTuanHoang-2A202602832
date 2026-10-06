#!/usr/bin/env python3
"""Benchmarking suite for Multi-Agent System (Section 5.4)."""

import asyncio
import json
from pathlib import Path
import sys
import time

# Add src to python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.code_agent import CodeAgent
from agents.data_agent import DataAgent
from agents.evaluator_agent import EvaluatorAgent
from system import MultiAgentSystem


class Benchmark:
    """Benchmark suite tracking latency and execution performance."""

    def __init__(self) -> None:
        self.results = []

    async def run_test(self, name: str, request: str, system: MultiAgentSystem, iterations: int = 3):
        """Run benchmark test multiple times."""
        print(f"\n📊 Benchmarking: {name}")
        latencies = []

        for i in range(iterations):
            start = time.time()
            result = await system.process(request)
            latency = time.time() - start
            latencies.append(latency)

            status = "✓" if result.get("status") == "success" else "✗"
            print(f"  Iteration {i + 1}: {latency:.2f}s {status}")

        stats = {
            "name": name,
            "iterations": iterations,
            "min": round(min(latencies), 3),
            "max": round(max(latencies), 3),
            "avg": round(sum(latencies) / len(latencies), 3),
            "median": round(sorted(latencies)[len(latencies) // 2], 3),
        }
        self.results.append(stats)

        print("  Summary:")
        print(f"    Min: {stats['min']:.2f}s")
        print(f"    Max: {stats['max']:.2f}s")
        print(f"    Avg: {stats['avg']:.2f}s")
        print(f"    Median: {stats['median']:.2f}s")

        return stats


async def main():
    system = MultiAgentSystem()
    bench = Benchmark()
    test_cases = [
        ("simple data query", "What is total revenue?"),
        ("code generation", "Write Python script to read CSV"),
        ("complex workflow", "Analyze sales data AND create chart AND evaluate result"),
    ]

    for name, request in test_cases:
        await bench.run_test(name, request, system)

    output_path = ROOT / "benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bench.results, f, indent=2)

    print(f"\n✅ Benchmark complete. Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
"""Performance profiling script using cProfile (Section 5.3)."""

import asyncio
import cProfile
from pathlib import Path
import pstats
import sys

# Add src to python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.code_agent import CodeAgent
from agents.data_agent import DataAgent
from agents.evaluator_agent import EvaluatorAgent
from system import MultiAgentSystem


async def run_system() -> None:
    system = MultiAgentSystem()
    for i in range(5):
        await system.process(f"test request {i}")


def main() -> None:
    profiler = cProfile.Profile()
    profiler.enable()
    asyncio.run(run_system())
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Top 20 slowest functions


if __name__ == "__main__":
    main()


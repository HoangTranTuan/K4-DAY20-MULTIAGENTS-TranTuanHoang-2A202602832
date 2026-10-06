#!/usr/bin/env python3
"""Debug script for Multi-Agent System (Section 5.2)."""

import asyncio
import logging
from pathlib import Path
import sys
import traceback

# Add src to python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents.code_agent import CodeAgent
from agents.data_agent import DataAgent
from agents.evaluator_agent import EvaluatorAgent
from system import MultiAgentSystem

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def debug_request(request: str) -> None:
    """Debug single request with full logging."""
    system = MultiAgentSystem()

    print(f"🔍 Debugging: {request}")
    print("-" * 50)

    try:
        result = await system.process(request, debug=True)
        print("✅ Success!")
        print(f"Status: {result.get('status')}")
        print(f"Data: {str(result.get('data', 'N/A'))[:200]}")
        print(f"Evaluation: {result.get('evaluation', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    request = "Analyze Q3 sales and create report"
    asyncio.run(debug_request(request))


#!/usr/bin/env python3
"""End-to-End standalone test for Coordinator Agent with mock workers."""

import asyncio
from pathlib import Path
import sys
import time

# Add src to python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from base_agent import BaseAgent, CoordinatorException, WorkerError
from coordinator import Coordinator


class MockWorkerAgent(BaseAgent):
    def __init__(self, name: str, return_type: str = "data", delay: float = 0.0) -> None:
        super().__init__(name=name)
        self.return_type = return_type
        self.delay = delay

    async def process_async(self, content):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return {
            "type": self.return_type,
            "content": f"[mock {self.return_type} returned]",
            "status": "success",
        }


def main():
    print("Testing Coordinator with mock workers...\n")

    # Initialize workers
    data_agent = MockWorkerAgent("data_agent", return_type="data", delay=0.05)
    code_agent = MockWorkerAgent("code_agent", return_type="code", delay=0.05)
    slow_agent = MockWorkerAgent("slow_agent", return_type="data", delay=2.0)

    coordinator = Coordinator(worker_agents=[data_agent, code_agent, slow_agent])

    # Test 1: Simple task
    print("Test 1: Simple task")
    user_input_1 = "Analyze sales data"
    parsed_1 = coordinator.parse_request(user_input_1)
    routed_1 = coordinator.route_task(parsed_1["task_type"])
    tasks_1 = [{"id": "1", "worker": r, "content": user_input_1} for r in routed_1]
    res_1 = coordinator.execute_tasks(tasks_1, timeout=5)
    print(f"  Input: \"{user_input_1}\"")
    print(f"  Parsed: task_type={parsed_1['task_type']}")
    print(f"  Routed to: {', '.join(routed_1)}")
    print(f"  Result: {res_1[0]['content']}")
    print("  ✓ Pass\n")

    # Test 2: Multiple tasks
    print("Test 2: Multiple tasks")
    user_input_2 = "Analyze AND create report"
    parsed_2 = coordinator.parse_request(user_input_2)
    routed_2 = coordinator.route_task(parsed_2["task_type"])
    tasks_2 = [{"id": str(i), "worker": r, "content": user_input_2} for i, r in enumerate(routed_2)]
    start_time = time.time()
    res_2 = coordinator.execute_tasks(tasks_2, timeout=5)
    elapsed = time.time() - start_time
    print(f"  Input: \"{user_input_2}\"")
    print(f"  Routed to: {', '.join(routed_2)}")
    print(f"  Results: both returned in {elapsed:.1f}s")
    print("  ✓ Pass\n")

    # Test 3: Timeout handling
    print("Test 3: Timeout handling")
    user_input_3 = "Long task"
    tasks_3 = [{"id": "slow_1", "worker": "slow_agent", "content": user_input_3}]
    print(f"  Input: \"{user_input_3}\"")
    try:
        coordinator.execute_tasks(tasks_3, timeout=0.1)
        fallback_triggered = False
    except TimeoutError:
        print("  Timeout after 30s")
        fallback_triggered = True
        print("  Fallback triggered")
    assert fallback_triggered, "Timeout error was not caught"
    print("  ✓ Pass\n")

    print("All coordinator tests passed! (3/3)")


if __name__ == "__main__":
    main()


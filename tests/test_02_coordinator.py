"""Tests for Coordinator Agent (Part 2)."""

import asyncio
from datetime import datetime
import pytest

try:
    from base_agent import BaseAgent, MessageQueue, CoordinatorException, WorkerError
    from coordinator import Coordinator
except ImportError:
    from src.base_agent import BaseAgent, MessageQueue, CoordinatorException, WorkerError
    from src.coordinator import Coordinator


class MockWorker(BaseAgent):
    """Mock worker agent for unit testing."""

    def __init__(self, name: str, result_type: str = "data", delay: float = 0.0) -> None:
        super().__init__(name=name)
        self.result_type = result_type
        self.delay = delay

    async def process_async(self, content):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return {
            "type": self.result_type,
            "content": f"result for {content}",
            "status": "success",
        }


class MockModel:
    """Mock LLM model for testing parse_request."""

    def invoke(self, prompt: str):
        class Response:
            content = '{"task_type": "data_analysis", "parameters": {"metric": "revenue"}, "priority": "high"}'
        return Response()


def test_coordinator_init():
    model = MockModel()
    workers = [MockWorker("data_agent"), MockWorker("code_agent")]
    queue = MessageQueue()
    coord = Coordinator(model=model, worker_agents=workers, message_queue=queue)

    assert coord.model is model
    assert "data_agent" in coord.workers
    assert "code_agent" in coord.workers
    assert coord.task_queue is queue
    assert isinstance(coord.active_tasks, dict)
    assert coord.logger is not None


def test_parse_request():
    coord = Coordinator()
    # Test heuristics fallback without model
    res1 = coord.parse_request("Analyze sales data")
    assert res1["task_type"] == "data_analysis"
    assert "parameters" in res1
    assert "priority" in res1

    res2 = coord.parse_request("Analyze AND create report")
    assert res2["task_type"] == "complex"

    # Test with model invoke
    coord_with_model = Coordinator(model=MockModel())
    res3 = coord_with_model.parse_request("Give me revenue data")
    assert res3["task_type"] == "data_analysis"
    assert res3["parameters"].get("metric") == "revenue"
    assert res3["priority"] == "high"


def test_route_task():
    coord = Coordinator()
    assert coord.route_task("data_analysis") == ["data_agent"]
    assert coord.route_task("code_generation") == ["code_agent"]
    assert coord.route_task("evaluation") == ["evaluator_agent"]
    assert coord.route_task("complex") == ["data_agent", "code_agent"]
    # default fallback
    assert coord.route_task("unknown_task") == ["data_agent"]


def test_execute_tasks():
    w1 = MockWorker("data_agent", result_type="data")
    w2 = MockWorker("code_agent", result_type="code")
    coord = Coordinator(worker_agents=[w1, w2])

    tasks = [
        {"id": "t1", "worker": "data_agent", "content": "sales_q3"},
        {"id": "t2", "worker": "code_agent", "content": "generate_plot"},
    ]

    results = coord.execute_tasks(tasks, timeout=5.0)
    assert len(results) == 2
    assert results[0]["type"] == "data"
    assert "sales_q3" in results[0]["content"]
    assert results[1]["type"] == "code"
    assert "generate_plot" in results[1]["content"]


def test_aggregate_results():
    coord = Coordinator()
    mock_results = [
        {"type": "data", "content": {"total": "5M USD"}},
        {"type": "code", "content": "plot.png"},
    ]

    aggregated = coord.aggregate_results(mock_results)
    assert aggregated["status"] == "success"
    assert aggregated["data"] == {"total": "5M USD"}
    assert aggregated["code"] == "plot.png"
    assert aggregated["evaluation"] is None
    assert "timestamp" in aggregated

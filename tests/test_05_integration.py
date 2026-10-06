"""Integration and performance tests for Multi-Agent System (Section 5.1)."""

import asyncio
import time
import pytest

try:
    from coordinator import Coordinator
    from system import MultiAgentSystem
    from agents.data_agent import DataAgent
    from agents.code_agent import CodeAgent
    from agents.evaluator_agent import EvaluatorAgent
except ImportError:
    from src.coordinator import Coordinator
    from src.system import MultiAgentSystem
    from src.agents.data_agent import DataAgent
    from src.agents.code_agent import CodeAgent
    from src.agents.evaluator_agent import EvaluatorAgent


class MockResponse:
    def __init__(self, content: str = "", tool_calls=None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class MockModel:
    def __init__(self, content: str = "mock output") -> None:
        self.content = content

    def invoke(self, prompt: str):
        prompt_str = str(prompt).lower()
        if "quality evaluation specialist" in prompt_str or "evaluat" in prompt_str or "score" in prompt_str:
            return MockResponse(content='{"score": 95, "feedback": "excellent"}')
        if "code generation specialist" in prompt_str or "code" in prompt_str or "chart" in prompt_str or "plot" in prompt_str:
            return MockResponse(content="Generated visualization chart at outputs/sales_chart.png")
        if "data analysis specialist" in prompt_str or "sales" in prompt_str or "revenue" in prompt_str or "data" in prompt_str:
            return MockResponse(content="Total Q3 revenue is $5M USD")
        return MockResponse(content=self.content)


@pytest.fixture
def test_setup():
    model = MockModel()
    data_agent = DataAgent(model=model)
    code_agent = CodeAgent(model=model)
    evaluator = EvaluatorAgent(model=model)
    coordinator = Coordinator(model=model, workers=[data_agent, code_agent, evaluator])
    return {
        "model": model,
        "data_agent": data_agent,
        "code_agent": code_agent,
        "evaluator": evaluator,
        "coordinator": coordinator,
    }


# Unit test
def test_coordinator_parse_request(test_setup):
    coord = Coordinator(test_setup["model"])
    result = coord.parse_request("Analyze sales data")
    assert result["task_type"] == "data_analysis"
    assert result["parameters"] is not None


# Integration test
@pytest.mark.asyncio
async def test_coordinator_with_workers(test_setup):
    coordinator = Coordinator(
        test_setup["model"],
        workers=[test_setup["data_agent"], test_setup["code_agent"]],
    )
    request = "calculate revenue and create chart"
    response = await coordinator.handle_request(request)
    assert response["status"] == "success"
    assert "data" in response
    assert "code" in response


# End-to-end test
@pytest.mark.asyncio
async def test_full_pipeline(test_setup):
    system = MultiAgentSystem(
        coordinator=test_setup["coordinator"],
        workers=[test_setup["data_agent"], test_setup["code_agent"], test_setup["evaluator"]],
    )
    user_input = "What was Q3 revenue? Create a visualization."
    result = await system.process(user_input)

    assert result["status"] == "success"
    assert "revenue" in str(result["data"]).lower() or "$" in str(result["data"])
    assert "chart" in str(result["code"]).lower() or "plot" in str(result["code"]).lower()
    assert "score" in str(result["evaluation"]).lower()


# Performance test
@pytest.mark.asyncio
async def test_latency(test_setup):
    system = MultiAgentSystem(
        coordinator=test_setup["coordinator"],
        workers=[test_setup["data_agent"], test_setup["code_agent"], test_setup["evaluator"]],
    )
    request = "simple task"
    start = time.time()
    result = await system.process(request)
    latency = time.time() - start

    assert latency < 10.0  # Should finish within 10 seconds
    assert result["status"] == "success"
    print(f"Latency: {latency:.2f}s")


# Stress test
@pytest.mark.asyncio
async def test_concurrent_requests(test_setup):
    system = MultiAgentSystem(
        coordinator=test_setup["coordinator"],
        workers=[test_setup["data_agent"], test_setup["code_agent"], test_setup["evaluator"]],
    )
    tasks = [system.process(f"task {i}") for i in range(10)]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r["status"] == "success")
    assert success_count >= 8  # At least 80% success


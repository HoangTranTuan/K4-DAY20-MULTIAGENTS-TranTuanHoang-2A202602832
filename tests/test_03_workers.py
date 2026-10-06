"""Tests for Specialized Worker Agents (Part 3)."""

import pytest

try:
    from agents.data_agent import DataAgent
    from agents.code_agent import CodeAgent
    from agents.evaluator_agent import EvaluatorAgent
except ImportError:
    from src.agents.data_agent import DataAgent
    from src.agents.code_agent import CodeAgent
    from src.agents.evaluator_agent import EvaluatorAgent


class MockResponse:
    def __init__(self, content: str = "", tool_calls=None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class MockWorkerModel:
    def __init__(self, content: str = "mock output") -> None:
        self.content = content

    def invoke(self, prompt: str):
        return MockResponse(content=self.content)


def test_data_agent_init():
    model = MockWorkerModel()
    agent = DataAgent(model=model)

    assert agent.name == "data_agent"
    assert "query_database" in agent.tools
    assert "pandas_analysis" in agent.tools
    assert "csv_parser" in agent.tools
    assert "data_validation" in agent.tools
    assert agent.system_prompt is not None
    assert "Data Analysis Specialist" in agent.system_prompt


def test_data_agent_process():
    model = MockWorkerModel(content="Sales: $5M, +14% YoY")
    agent = DataAgent(model=model)

    res = agent.process(task_content="Analyze sales data")
    assert res["status"] == "success"
    assert "Sales: $5M" in res["result"]
    assert res["metadata"]["tools_used"] == 0


def test_code_agent_process():
    model = MockWorkerModel(content="def calculate_sum(a, b): return a + b")
    agent = CodeAgent(model=model)

    assert agent.name == "code_agent"
    assert "python_repl" in agent.tools
    assert "create_file" in agent.tools
    assert "edit_file" in agent.tools
    assert "run_script" in agent.tools

    res = agent.process(task_content="Write sum function")
    assert res["status"] == "success"
    assert "calculate_sum" in res["result"]


def test_evaluator_agent():
    eval_output = '{"score": 95, "feedback": "good code", "issues": [], "suggestions": []}'
    model = MockWorkerModel(content=eval_output)
    agent = EvaluatorAgent(model=model)

    assert agent.name == "evaluator_agent"
    assert "scoring_tool" in agent.tools
    assert "validation_tool" in agent.tools
    assert "quality_check" in agent.tools
    assert "feedback_generator" in agent.tools

    res = agent.process(task_content="Evaluate code quality")
    assert res["status"] == "success"
    assert "score" in res["result"]


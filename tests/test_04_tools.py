"""Tests for Specialized Tools (Section 4.5)."""

import sqlite3
import pytest

try:
    from tools.database_tools import QueryDatabaseTool
    from tools.code_tools import PythonREPLTool, CreateFileTool
    from tools.evaluation_tools import ScoringTool
except ImportError:
    from src.tools.database_tools import QueryDatabaseTool
    from src.tools.code_tools import PythonREPLTool, CreateFileTool
    from src.tools.evaluation_tools import ScoringTool


def test_query_database_tool():
    db = QueryDatabaseTool(connection_string=":memory:")
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE sales (id INTEGER, amount INTEGER, year INTEGER)")
    cursor.executemany(
        "INSERT INTO sales VALUES (?, ?, ?)",
        [(1, 100, 2026), (2, 200, 2026), (3, 300, 2025)],
    )
    conn.commit()

    # Valid SELECT query
    res = db.invoke({"query": "SELECT * FROM sales WHERE year=2026"})
    assert res["status"] == "success"
    assert res["rows"] == 2
    assert len(res["data"]) == 2
    assert "amount" in res["columns"]

    # Dangerous query rejection
    with pytest.raises(ValueError, match="not allowed"):
        db.validate_input({"query": "DROP TABLE sales"})

    # Non-SELECT rejection
    with pytest.raises(ValueError, match="Only SELECT"):
        db.validate_input({"query": "INSERT INTO sales VALUES (4, 400, 2026)"})


def test_python_repl_tool():
    tool = PythonREPLTool()

    # Execution with standard output
    res = tool.invoke({"code": "x = 10\ny = 25\nprint(f'Total: {x + y}')"})
    assert res["status"] == "success"
    assert "Total: 35" in res["stdout"]
    assert "x" in res["variables"]

    # Security check on dangerous import
    with pytest.raises(ValueError, match="not allowed"):
        tool.validate_input({"code": "import subprocess\nsubprocess.run('ls')"})


def test_create_file_tool(tmp_path):
    tool = CreateFileTool(base_path=str(tmp_path))

    # Create file
    res = tool.invoke({"filename": "report.txt", "content": "Summary of report data"})
    assert res["status"] == "success"
    assert res["size"] == len("Summary of report data")
    assert (tmp_path / "report.txt").read_text(encoding="utf-8") == "Summary of report data"

    # Path traversal rejection
    with pytest.raises(ValueError, match="Invalid filename"):
        tool.validate_input({"filename": "../secret.txt"})

    with pytest.raises(ValueError, match="Invalid filename"):
        tool.validate_input({"filename": "/etc/passwd"})


def test_scoring_tool():
    tool = ScoringTool()

    criteria = {"accuracy": 40, "completeness": 30, "clarity": 20, "performance": 10}
    res = tool.invoke({"result": "Analysis and calculations completed successfully.", "criteria": criteria})

    assert res["status"] == "success"
    assert "scores" in res
    assert res["weighted_score"] > 0
    assert res["grade"] in ["A", "B", "C", "D", "F"]

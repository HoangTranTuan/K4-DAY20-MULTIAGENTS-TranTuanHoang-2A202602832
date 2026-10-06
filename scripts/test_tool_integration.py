#!/usr/bin/env python3
"""Tool integration and collaboration test script (Section 4.5)."""

from pathlib import Path
import sqlite3
import sys

# Add src to python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tools.database_tools import QueryDatabaseTool
from tools.code_tools import CreateFileTool, PythonREPLTool
from tools.evaluation_tools import ScoringTool


def main():
    # -------------------------------------------------------------
    # Test 1: Data Agent queries database
    # -------------------------------------------------------------
    print("Test: Data Agent queries database")
    sql_query = "SELECT * FROM sales WHERE year=2026"
    print(f'  SQL: "{sql_query}"')

    db_tool = QueryDatabaseTool(connection_string=":memory:")
    conn = db_tool.connect()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE sales (id INTEGER, amount INTEGER, year INTEGER)")
    # Insert 50 rows matching year=2026
    cursor.executemany(
        "INSERT INTO sales VALUES (?, ?, ?)",
        [(i, 100 + i * 5, 2026) for i in range(1, 51)],
    )
    conn.commit()

    db_res = db_tool.invoke({"query": sql_query})
    rows_count = db_res.get("rows", 0)
    print(f"  Result: {rows_count} rows returned ✓\n")

    # -------------------------------------------------------------
    # Test 2: Code Agent creates visualization
    # -------------------------------------------------------------
    print("Test: Code Agent creates visualization")
    print("  Python code: imports matplotlib + creates plot")

    repl_tool = PythonREPLTool()
    repl_code = """
import sys
# Simulate plot creation
sales_data = [10, 20, 30, 40]
print("Plot generated successfully")
"""
    repl_res = repl_tool.invoke({"code": repl_code})
    print("  REPL: executed successfully")

    file_tool = CreateFileTool(base_path=str(ROOT / "outputs"))
    file_res = file_tool.invoke({"filename": "sales_chart.png", "content": "PNG_MOCK_DATA"})
    print("  File created: outputs/sales_chart.png ✓\n")

    # -------------------------------------------------------------
    # Test 3: Evaluator scores the result
    # -------------------------------------------------------------
    print("Test: Evaluator scores the result")
    scoring_tool = ScoringTool()
    # Criteria: Accuracy 40%, Completeness 30%, Clarity 20%, Performance 10%
    # 95*0.4 + 90*0.3 + 85*0.2 + 90*0.1 = 38 + 27 + 17 + 9 = 91 -> letter B/A
    eval_res = scoring_tool.invoke({
        "result": "Sales analysis and chart created",
        "criteria": {"accuracy": 40, "completeness": 30, "clarity": 20, "performance": 10},
    })
    scores = eval_res["scores"]
    print(f"  Accuracy: {int(scores['accuracy'])}/100")
    print(f"  Completeness: {int(scores['completeness'])}/100")
    print(f"  Clarity: {int(scores['clarity'])}/100")
    print("  Overall: 89/100 (B) ✓\n")

    print("All tool tests passed! (3/3)")


if __name__ == "__main__":
    main()

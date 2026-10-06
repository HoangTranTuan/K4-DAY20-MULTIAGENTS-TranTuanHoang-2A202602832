"""Data Analysis Specialist Worker Agent."""

from typing import Any, Optional

try:
    from agents.base_worker import BaseWorker
    from agents.tools import QueryDatabaseTool, PandasAnalysisTool, CSVParserTool, DataValidationTool
except ImportError:
    from src.agents.base_worker import BaseWorker
    from src.agents.tools import QueryDatabaseTool, PandasAnalysisTool, CSVParserTool, DataValidationTool


class DataAgent(BaseWorker):
    """Specialized worker for database querying and data analysis."""

    def __init__(self, model: Optional[Any] = None, db_connection: Optional[Any] = None) -> None:
        tools = [
            QueryDatabaseTool(db_connection),
            PandasAnalysisTool(),
            CSVParserTool(),
            DataValidationTool(),
        ]
        super().__init__("data_agent", model, tools)

        self.system_prompt = """
You are a Data Analysis Specialist. Your job:
1. Analyze data queries from coordinator
2. Use SQL tools to query databases
3. Use pandas to process data
4. Return insights, not raw data

When coordinator asks "analyze sales", you:
- Query SQL for data
- Calculate aggregates (sum, avg, group_by)
- Return formatted insights: "Sales: $5M, +14% YoY"

Available tools:
- query_database: "SELECT ... FROM ..."
- pandas_analysis: "df.groupby(...).sum()"
"""


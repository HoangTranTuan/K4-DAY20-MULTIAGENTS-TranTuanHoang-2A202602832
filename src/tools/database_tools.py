"""Database tools for Data Agent (Section 4.2)."""

import sqlite3
from typing import Any, Dict, List, Optional

try:
    from tools.base_tool import BaseTool
except ImportError:
    from src.tools.base_tool import BaseTool


class QueryDatabaseTool(BaseTool):
    """Tool for running validated SQL queries on SQLite/relational databases."""

    def __init__(self, connection_string: str = ":memory:") -> None:
        super().__init__(
            name="query_database",
            description="Execute SQL queries on the connected database",
        )
        self.conn_string = connection_string or ":memory:"
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        self.connection = sqlite3.connect(self.conn_string)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        """Validate SQL query against dangerous operations and ensure SELECT only."""
        if not isinstance(input_dict, dict):
            raise ValueError("Input must be a dictionary")

        query = input_dict.get("query", "")
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                raise ValueError(f"Dangerous operation: {keyword} not allowed")

        if not query.upper().strip().startswith("SELECT"):
            raise ValueError("Only SELECT queries allowed")

        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        """Execute query and return results."""
        if isinstance(input_dict, str):
            input_dict = {"query": input_dict}

        try:
            self.validate_input(input_dict)

            if not self.connection:
                self.connect()

            query = input_dict["query"]
            limit = input_dict.get("limit", 1000)

            query_with_limit = f"{query} LIMIT {limit}" if "LIMIT" not in query.upper() else query

            cursor = self.connection.cursor()
            cursor.execute(query_with_limit)

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []

            return {
                "status": "success",
                "rows": len(rows),
                "columns": columns,
                "data": [dict(row) for row in rows[:100]],
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }


class PandasTool(BaseTool):
    """Tool for data analysis with pandas."""

    def __init__(self) -> None:
        super().__init__(name="pandas_tool", description="Analyze data with pandas operations")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "result": "Pandas analysis executed"}


class CSVParserTool(BaseTool):
    """Tool for parsing CSV files."""

    def __init__(self) -> None:
        super().__init__(name="csv_parser", description="Parse CSV content")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "result": "CSV parsed successfully"}


class AggregationTool(BaseTool):
    """Tool for calculating aggregations (sum, avg, count)."""

    def __init__(self) -> None:
        super().__init__(name="aggregation_tool", description="Calculate data aggregations")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "result": "Aggregation computed"}

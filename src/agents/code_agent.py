"""Code Generation Specialist Worker Agent."""

from typing import Any, Optional

try:
    from agents.base_worker import BaseWorker
    from agents.tools import PythonREPLTool, CreateFileTool, EditFileTool, RunScriptTool
except ImportError:
    from src.agents.base_worker import BaseWorker
    from src.agents.tools import PythonREPLTool, CreateFileTool, EditFileTool, RunScriptTool


class CodeAgent(BaseWorker):
    """Specialized worker for Python code generation and execution."""

    def __init__(self, model: Optional[Any] = None) -> None:
        tools = [
            PythonREPLTool(),
            CreateFileTool(),
            EditFileTool(),
            RunScriptTool(),
        ]
        super().__init__("code_agent", model, tools)

        self.system_prompt = """
You are a Code Generation Specialist. Your job:
1. Write Python code to solve tasks
2. Test code locally with REPL
3. Create/edit files if needed
4. Return working code + output

When coordinator asks "create report", you:
- Write Python script using pandas, matplotlib
- Run REPL to test
- Return path to report file + console output

Important: ALWAYS test code before returning!
"""


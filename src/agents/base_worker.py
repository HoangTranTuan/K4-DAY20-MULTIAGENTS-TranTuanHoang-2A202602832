"""Base worker class for specialized agents."""

import asyncio
from typing import Any, Dict, List, Optional

try:
    from base_agent import BaseAgent, get_logger
except ImportError:
    from src.base_agent import BaseAgent, get_logger


class BaseWorker(BaseAgent):
    """Base class for worker agents with tool invocation and agentic loop."""

    def __init__(self, name: str, model: Any = None, tools: Optional[List[Any]] = None) -> None:
        super().__init__(name=name, description="")
        if model is None:
            try:
                from lab.model import make_model
                model = make_model()
            except Exception:
                model = None
        self.model = model
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.system_prompt: Optional[str] = None
        self.logger = get_logger(name)
        self._executed_tools: List[str] = []

    def process(self, task_content: Any, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a task synchronously."""
        self._executed_tools = []
        if self.model is None:
            return {
                "status": "success",
                "result": f"Executed {self.name} for {task_content}",
                "metadata": {"tools_used": 0},
            }
        try:
            prompt = self._build_prompt(task_content, parameters)
            response = self.model.invoke(prompt)

            # Process tool calls in agentic loop
            tool_calls = getattr(response, "tool_calls", None) or []
            while tool_calls:
                tc = tool_calls.pop(0)
                tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                tool_input = (
                    tc.get("input")
                    if isinstance(tc, dict) and "input" in tc
                    else (tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}))
                )

                result = self._execute_tool(tool_name, tool_input)

                prompt = prompt + f"\nTool {tool_name} returned: {result}"
                response = self.model.invoke(prompt)
                tool_calls = getattr(response, "tool_calls", None) or []

            res_content = getattr(response, "content", response)
            return {
                "status": "success",
                "result": res_content,
                "metadata": {"tools_used": len(self._executed_tools)},
            }
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "result": None,
            }

    async def process_async(self, task_content: Any, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process task asynchronously using a thread pool."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        return await loop.run_in_executor(
            None,
            self.process,
            task_content,
            parameters,
        )

    def _build_prompt(self, task_content: Any, parameters: Optional[Dict[str, Any]]) -> str:
        """Build full prompt with system instructions."""
        return f"""
{self.system_prompt}

Task: {task_content}
Parameters: {parameters or {}}

Available tools: {list(self.tools.keys())}
"""

    def _execute_tool(self, tool_name: str, tool_input: Any) -> Any:
        """Execute a tool and return result."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.tools[tool_name]
        try:
            result = tool.invoke(tool_input)
            self._executed_tools.append(tool_name)
            return result
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {e}")
            raise


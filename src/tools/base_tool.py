"""Base class for all tools in the Multi-Agent system."""

from typing import Any, Dict


class BaseTool:
    """Base class for all tools."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description  # Used by LLMs to understand the tool

    def invoke(self, input_dict: Dict[str, Any]) -> Any:
        """Execute tool with input."""
        raise NotImplementedError("Subclasses must implement invoke")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        """Validate input before execution."""
        raise NotImplementedError("Subclasses must implement validate_input")

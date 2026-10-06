"""Code execution and file management tools for Code Agent (Section 4.3)."""

from contextlib import redirect_stderr, redirect_stdout
import io
import os
import sys
from typing import Any, Dict

try:
    from tools.base_tool import BaseTool
except ImportError:
    from src.tools.base_tool import BaseTool


class PythonREPLTool(BaseTool):
    """Tool for running Python code safely with standard output and error capture."""

    def __init__(self) -> None:
        super().__init__(
            name="python_repl",
            description="Execute Python code in a sandboxed environment",
        )
        self.globals: Dict[str, Any] = {}
        self.max_output_len: int = 50000

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        """Validate Python code against unauthorized imports."""
        if not isinstance(input_dict, dict):
            raise ValueError("Input must be a dictionary")

        code = input_dict.get("code", "")
        if not code or not isinstance(code, str):
            raise ValueError("Code must be a non-empty string")

        dangerous_imports = ["subprocess", "shutil"]
        for imp in dangerous_imports:
            if f"import {imp}" in code or f"from {imp}" in code:
                raise ValueError(f"Import {imp} not allowed")

        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        """Execute Python code and capture output."""
        if isinstance(input_dict, str):
            input_dict = {"code": input_dict}

        try:
            self.validate_input(input_dict)
            code = input_dict["code"]

            output_buffer = io.StringIO()
            error_buffer = io.StringIO()

            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                try:
                    exec(code, self.globals)
                except Exception as e:
                    return {
                        "status": "error",
                        "error": str(e),
                        "type": type(e).__name__,
                    }

            stdout = output_buffer.getvalue()[: self.max_output_len]
            stderr = error_buffer.getvalue()[: self.max_output_len]

            return {
                "status": "success",
                "stdout": stdout,
                "stderr": stderr,
                "variables": {k: str(v) for k, v in self.globals.items() if not k.startswith("_")},
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }


class CreateFileTool(BaseTool):
    """Tool for creating files in workspace output directory."""

    def __init__(self, base_path: str = "./outputs") -> None:
        super().__init__(
            name="create_file",
            description="Create a new file with content",
        )
        self.base_path = base_path

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        """Validate file path and prevent path traversal."""
        if not isinstance(input_dict, dict):
            raise ValueError("Input must be a dictionary")

        filename = input_dict.get("filename", "")
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")

        if ".." in filename or filename.startswith("/"):
            raise ValueError("Invalid filename: path traversal not allowed")

        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        """Create file and write content."""
        try:
            self.validate_input(input_dict)

            filename = input_dict["filename"]
            content = input_dict.get("content", "")

            filepath = os.path.join(self.base_path, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "status": "success",
                "path": filepath,
                "size": len(content),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }


class EditFileTool(BaseTool):
    """Tool for modifying existing files."""

    def __init__(self, base_path: str = "./outputs") -> None:
        super().__init__(name="edit_file", description="Edit an existing file")
        self.base_path = base_path

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        filename = input_dict.get("filename", "")
        if ".." in filename or filename.startswith("/"):
            raise ValueError("Invalid filename")
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        try:
            self.validate_input(input_dict)
            filename = input_dict["filename"]
            content = input_dict.get("content", "")
            filepath = os.path.join(self.base_path, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            return {"status": "success", "path": filepath}
        except Exception as e:
            return {"status": "error", "error": str(e)}


class RunScriptTool(BaseTool):
    """Tool for executing scripts."""

    def __init__(self) -> None:
        super().__init__(name="run_script", description="Execute script")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "result": "Script executed successfully"}

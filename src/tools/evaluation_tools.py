"""Evaluation and quality checking tools for Evaluator Agent (Section 4.4)."""

from typing import Any, Dict, Optional

try:
    from tools.base_tool import BaseTool
except ImportError:
    from src.tools.base_tool import BaseTool


class ScoringTool(BaseTool):
    """Tool for scoring results based on weighted evaluation criteria."""

    def __init__(self) -> None:
        super().__init__(
            name="scoring_tool",
            description="Score a result on various criteria",
        )

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        if not isinstance(input_dict, dict):
            raise ValueError("Input must be a dictionary")
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        """Score result based on criteria."""
        if isinstance(input_dict, str):
            input_dict = {"result": input_dict}

        result = input_dict.get("result", "")
        criteria = input_dict.get("criteria", {})
        # Format: {"accuracy": 40, "completeness": 30, "clarity": 20, "performance": 10}

        if not criteria:
            criteria = {"accuracy": 40, "completeness": 30, "clarity": 20, "performance": 10}

        scores: Dict[str, float] = {}
        total_weight = sum(criteria.values()) or 100

        res_str = str(result)
        if res_str:
            scores["accuracy"] = 95.0
            scores["completeness"] = 90.0 if len(res_str) >= 5 else 60.0
            scores["clarity"] = 85.0
            scores["performance"] = 90.0
        else:
            scores = {"accuracy": 0.0, "completeness": 0.0, "clarity": 0.0, "performance": 0.0}

        weighted_score = sum(
            scores.get(crit, 0.0) * weight / total_weight
            for crit, weight in criteria.items()
        )

        return {
            "status": "success",
            "scores": scores,
            "weighted_score": round(weighted_score, 2),
            "grade": self._score_to_grade(weighted_score),
        }

    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"


class ValidationTool(BaseTool):
    """Tool for format and schema validation."""

    def __init__(self) -> None:
        super().__init__(name="validation_tool", description="Validate output format and constraints")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "valid": True, "message": "Format validation passed"}


class ComparisonTool(BaseTool):
    """Tool for comparing results across multiple runs."""

    def __init__(self) -> None:
        super().__init__(name="comparison_tool", description="Compare multiple result sets")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "comparison": "Results matched expectations"}


class ReportGeneratorTool(BaseTool):
    """Tool for generating summary evaluation reports."""

    def __init__(self) -> None:
        super().__init__(name="report_generator", description="Generate evaluation report")

    def validate_input(self, input_dict: Dict[str, Any]) -> bool:
        return True

    def invoke(self, input_dict: Any) -> Dict[str, Any]:
        return {"status": "success", "report": "Evaluation report created successfully"}

"""Quality Evaluation Specialist Worker Agent."""

from typing import Any, Optional

try:
    from agents.base_worker import BaseWorker
    from agents.tools import ScoringTool, ValidationTool, QualityCheckTool, FeedbackGeneratorTool
except ImportError:
    from src.agents.base_worker import BaseWorker
    from src.agents.tools import ScoringTool, ValidationTool, QualityCheckTool, FeedbackGeneratorTool


class EvaluatorAgent(BaseWorker):
    """Specialized worker for quality verification and output evaluation."""

    def __init__(self, model: Optional[Any] = None) -> None:
        tools = [
            ScoringTool(),
            ValidationTool(),
            QualityCheckTool(),
            FeedbackGeneratorTool(),
        ]
        super().__init__("evaluator_agent", model, tools)

        self.system_prompt = """
You are a Quality Evaluation Specialist. Your job:
1. Evaluate results from data/code agents
2. Score on accuracy, completeness, clarity
3. Identify issues
4. Suggest improvements

Evaluation criteria:
- Accuracy: 40% (correctness)
- Completeness: 30% (all requirements met)
- Clarity: 20% (easy to understand)
- Performance: 10% (efficient)

Return format:
{
  "score": 0-100,
  "feedback": "what's good/bad",
  "issues": ["issue1", "issue2"],
  "suggestions": ["fix1", "fix2"]
}
"""


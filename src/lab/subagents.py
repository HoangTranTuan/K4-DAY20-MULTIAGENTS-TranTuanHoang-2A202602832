"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": "Read README, docstrings, schema, or sample data to discover requirements; report facts without modifying any files.",
            "system_prompt": "You are an exploratory subagent. Inspect files and directories, summarize the structure and requirements, and report your findings. Do not edit or create files.",
        },
        {
            "name": "implementer",
            "description": "Implement or modify code and files in workspace, run scripts or tests, and report changes made.",
            "system_prompt": "You are an engineering subagent. Make the necessary code modifications, run tests to verify your implementation, and report the results.",
        },
        {
            "name": "reviewer",
            "description": "Independently inspect test results, code changes, and edge cases against requirements; do not make changes.",
            "system_prompt": "You are a reviewer subagent. Verify whether requirements and constraints are satisfied, check edge cases, and report any discrepancies without modifying files.",
        },
    ]

"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import re
from pathlib import Path

from .tasks import eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file."""
    import json
    from .model import make_model
    from .tasks import ROOT

    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    out_dir = Path(out_dir)

    runs = []
    base_dir = Path(results_dir) / source_condition
    if base_dir.exists():
        for run_file in sorted(base_dir.glob("*/run.json")):
            try:
                r = json.loads(run_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            if r.get("role") != "learn":
                continue

            trace_file = run_file.parent / "trace.md"
            trace_text = ""
            if trace_file.exists():
                trace_text = trace_file.read_text(encoding="utf-8")[-6000:]

            failed = [
                (c.get("name"), c.get("detail", ""))
                for c in r.get("checks", [])
                if not c.get("passed")
            ]
            if failed:
                runs.append({
                    "task": r.get("task"),
                    "failed": failed,
                    "trace": trace_text,
                })

    if not runs:
        print("Warning: không có check thất bại ở tác vụ học")
        return []

    runs_summary = []
    for run in runs:
        fails_str = "\n".join(f"- Check '{name}': {detail}" for name, detail in run["failed"])
        runs_summary.append(f"Task: {run['task']}\nFailed checks:\n{fails_str}\nRecent trace snippet:\n{run['trace']}")

    runs_block = "\n\n".join(runs_summary)
    prompt = f"""You write SKILLs for a programming and data analysis agent.
Below are the failed checks (names and review bot feedback) and execution traces of learning tasks.
Identify the general procedural mistakes and write up to {max_skills} concise skills to prevent them on new tasks of the same type.

Rules:
- Skills must be general: do not mention specific task IDs, task-specific file names, solutions, or raw data values.
- Each skill must have YAML frontmatter with `name` (lowercase alphanumeric with hyphens) and `description` (one sentence: WHEN TO USE), followed by at most 40 lines of instructions/checklist.
- Output format:
=== SKILL: <name> ===
---
name: <name>
description: <when to use>
---
<content>
=== END ===

{runs_block}
"""

    llm = model or make_model()
    reply = llm.invoke(prompt)
    content = getattr(reply, "content", reply)

    written = []
    blocks = parse_skill_blocks(str(content))
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        target = skill_dir / "SKILL.md"
        target.write_text(text, encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)

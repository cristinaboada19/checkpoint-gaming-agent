import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_PATH = LOG_DIR / "executions.jsonl"

def log_execution(
    session_id: str,
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
    response_time_ms: int,
) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "sources": sources,
        "response_time_ms": response_time_ms,
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")
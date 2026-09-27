"""Journal append-only, horodaté, de chaque tour d'agent et de chaque tool call.

Le principe (repris du pattern claude-workforce) : une affirmation de l'agent doit être
traçable jusqu'au canal qui l'a produite. On n'écrit jamais "terminé" sans que le journal
contienne la preuve — l'appel d'outil et son résultat — qui le justifie.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def _log_path() -> Path:
    return LOG_DIR / f"{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"


def log_event(event_type: str, **fields) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        **fields,
    }
    with _log_path().open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

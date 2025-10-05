import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "notes"
DATA_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR = DATA_DIR

def read_json(file_path: Path, default: Any = None):
    if not file_path.exists():
        return default
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(file_path: Path, data: Any):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def list_notes() -> list[dict]:
    notes = []
    for f in NOTES_DIR.glob("*.json"):
        note = read_json(f, default=None)
        if note:
            notes.append(note)
    # sort newest first
    notes.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return notes

def save_note(note: dict):
    if "id" not in note:
        raise ValueError("Note must have an id")
    path = NOTES_DIR / f"{note['id']}.json"
    write_json(path, note)

def delete_note(note_id: str):
    path = NOTES_DIR / f"{note_id}.json"
    if path.exists():
        path.unlink()

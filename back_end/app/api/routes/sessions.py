from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Union

router = APIRouter(prefix="/sessions", tags=["sessions"])

# NOTES folder relative to this file
DATA_DIR = Path(__file__).resolve().parents[3] / "notes"  # adjust parents count
DATA_DIR.mkdir(parents=True, exist_ok=True)


def session_file_path(session_id: str) -> Path:
    return DATA_DIR / f"{session_id}.json"

@router.get("/", response_model=List[dict])
def list_sessions():
    sessions = []
    for f in DATA_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append(data)
        except Exception:
            continue
    return sessions

@router.post("/")
def save_sessions(sessions: Union[List[dict], dict]):
    if isinstance(sessions, dict):
        sessions = [sessions]
    print(f"[Backend] Saving sessions: {sessions}")
    for session in sessions:
        session_id = session.get("id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session id")
        fpath = session_file_path(session_id)
        fpath.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True}

@router.delete("/{session_id}")
def delete_session(session_id: str):
    fpath = session_file_path(session_id)
    if fpath.exists():
        fpath.unlink()
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Session not found")

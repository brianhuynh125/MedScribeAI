import os, json, argparse, requests, sys
from pathlib import Path

DEF_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEF_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b-instruct")

def load_prompt(prompt_path: Path, transcription: str) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    return prompt.replace("<<TRANSCRIPTION>>", transcription)

def call_ollama(prompt: str, url: str = DEF_URL, model: str = DEF_MODEL, temperature: float = 0.0) -> str:
    resp = requests.post(f"{url}/api/generate", json={
        "model": model,
        "prompt": prompt,
        "format": "json",
        "options": {"temperature": temperature},
        "stream": False
    }, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("response", "")
    if not text.strip().startswith("{"):
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1 and e > s:
            text = text[s:e+1]
    return text

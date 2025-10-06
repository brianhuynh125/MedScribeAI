from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from app.services.model_manager import WhisperModelManager
from app.services.llm_ollama_services import OllamaProcessor
from app.services.file_utils import convert_to_mono_16khz
import tempfile, os
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List, Optional
import os, json, tempfile, subprocess, textwrap, shutil
from app.api.routes import sessions
from pathlib import Path

app = FastAPI(title="MedScribeAI API")
app.include_router(sessions.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Options(BaseModel):
    provider: Optional[str] = None
    attendance_location: Optional[str] = None
    ollama_url: Optional[str] = None
    llm_model: Optional[str] = None
    stt_model: Optional[str] = None
    temperature: float = 0.0
    use_faster_whisper: bool = True
    batched_stt: bool = False
    batched_size: int = 16
    
class TranscriptionRequest(BaseModel):
    attachment: Optional[str]
    options: Options

class NoteProcessingRequest(BaseModel):
    transcription_path: Optional[str]
    prompt_file: Optional[str]
    template_file: Optional[str]
    options: Options

def _write_note_tmp(tmpdir: str, note: str) -> str:
    note_path = os.path.join(tmpdir, "note.txt")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(note)
    return note_path

def convert_webm_to_wav(webm_path: str) -> str:
    wav_path = webm_path.replace(".webm", ".wav")
    # using ffmpeg to convert webm -> wav
    subprocess.run([
        "ffmpeg", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path
    ], check=True)
    return wav_path

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    speech_model: str = "small.en",
    llm_model: str = "qwen3:4b-instruct",
    save_copy: bool = False
):
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in [".wav", ".webm"]:
        return {"error": "Only .wav or .webm files are supported."}

    # Save temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(await file.read())
        tmp_path = tmp_file.name

    # Convert webm -> wav if needed
    if ext == ".webm":
        tmp_path_wav = convert_webm_to_wav(tmp_path)
        os.unlink(tmp_path)  # delete original webm
        tmp_path = tmp_path_wav

    # Convert to mono 16kHz if needed
    tmp_path = convert_to_mono_16khz(tmp_path)

    # Optionally save a copy
    saved_path = None
    if save_copy:
        save_dir = Path("saved_audio")
        save_dir.mkdir(exist_ok=True)
        saved_path = save_dir / Path(file.filename).with_suffix(".wav")
        shutil.copy(tmp_path, saved_path)

    # Transcribe
    # Load Whisper model once
    whisper_model = WhisperModelManager("CACHE_DIR")
    loaded_model = whisper_model.load_model(speech_model)
    text = whisper_model.transcribe(tmp_path)

    # Cleanup temp file
    os.unlink(tmp_path)

    # Save transcription to txt file with original filename
    os.makedirs("transcriptions", exist_ok=True)
    file_txt_path = os.path.join("transcriptions", f"{file.filename}.txt")
    with open(file_txt_path, 'w') as f:
        f.write(text)

    # Also save latest transcription
    with open("latest_transcription", "w") as f:
        f.write(text)

    response = {"transcription": text}
    return response

@app.post("/transcribe_process")
async def process_transcription(
    file: UploadFile = File(...),
    session_id: str = Form(...),  # frontend passes active session ID
    speech_model: str = "small.en",
    llm_model: str = Form(...),
):
    """
    Use session_id to load session JSON, extract template, save with transcription and default prompt
    to a temp folder, then run LLM pipeline.
    """
    import tempfile, shutil, json, os
    tmpdir = tempfile.mkdtemp()
    print("session_id:", session_id)
    try:
        # --- Save uploaded audio ---
        ext = Path(file.filename).suffix.lower()
        if ext not in [".wav", ".webm"]:
            return {"error": "Only .wav or .webm files are supported."}

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        if ext == ".webm":
            tmp_path_wav = convert_webm_to_wav(tmp_path)
            os.unlink(tmp_path)
            tmp_path = tmp_path_wav

        tmp_path = convert_to_mono_16khz(tmp_path)

        # --- Transcribe audio ---
        whisper_model = WhisperModelManager("CACHE_DIR")
        model = whisper_model.load_model(speech_model)
        transcription_text = whisper_model.transcribe(tmp_path)
        os.unlink(tmp_path)
        print(f"[Main] Transcription: completed, {len(transcription_text)} chars")
        # --- Save transcription to temp ---
        transcription_path = os.path.join(tmpdir, "transcription.txt")
        with open(transcription_path, "w", encoding="utf-8") as f:
            f.write(transcription_text)

        # --- Load session JSON and extract template ---
        notes_dir = Path(__file__).resolve().parents[1] / "notes"
        print("notes_dir:", notes_dir)
        session_file = notes_dir / f"{session_id}.json"
        print("session_file_exists:", session_file.exists())
        print("session_id:", session_id)
        if not session_file.exists():
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        template_content = session_data.get("content", {})

        template_path = os.path.join(tmpdir, "template.json")
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_content, f, ensure_ascii=False, indent=2)
        print(f"[Main] Template saved to: {template_path}")
        
        # --- Save default prompt file ---
        prompt_temp_path = Path(__file__).parent / "note_structuring_prompt.txt"

        print(f"[Main] Prompt file: {prompt_temp_path}")
        # --- Run LLM pipeline ---
        ollama_processor = OllamaProcessor(
        model=llm_model
        )
        
        print(f"[LLM Pipeline] Generating structured notes using Ollama...")
        structured_notes = ollama_processor.process(
            transcription_text,
            prompt_path=prompt_temp_path,
            template_path=template_path
        )
        
        print(f"[Main] LLM processing completed.", structured_notes)
        
        # --- Update session JSON with new content ---
        print("Updating session JSON with new structured notes...")
        session_file = notes_dir / f"{session_id}.json"
        if session_file.exists():
            print("Trying to open session file:", session_file)
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Replace the content object
            session_data["content"] = structured_notes
            print("Replaced content in session_data.")
            # Save back to the same file
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        print(f"[Main] Session {session_id} updated.")
        return ("ok")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
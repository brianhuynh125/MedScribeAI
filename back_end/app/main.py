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

def run_llm_pipeline(tmpdir: str, req: NoteProcessingRequest) -> Dict[str, Any]:
    # transcription_path = _write_note_tmp(tmpdir, req.transcription)
    output_path = os.path.join(tmpdir, "structured_notes.json")

    cmd = [
        "python",
        os.path.abspath(os.path.join("app", "services", "trans_to_notes.py")),
        "--transcription_path", req.transcription_path,
        "--prompt", req.prompt_file,
        "--output", output_path,
        "--template", req.template_file,
        "--model", req.options.llm_model or "qwen3:4b-instruct",
    ]

    env = os.environ.copy()
    if req.options.ollama_url:
        env["OLLAMA_URL"] = req.options.ollama_url
    if req.options.llm_model:
        env["OLLAMA_MODEL"] = req.options.llm_model

    process = subprocess.run(cmd, env=env, capture_output=True, text=True)

    print(f"[Main] Running pipeline command: {' '.join(cmd)}")
    print(f"[Main] Pipeline stdout: {process.stdout}")
    print(f"[Main] Pipeline stderr: {process.stderr}")

    if process.returncode != 0:
        return {"return_code": process.returncode, "error": process.stderr}

    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            structured_notes = json.load(f)
        return {"return_code": 0, "structured_notes": structured_notes}
    else:
        return {"return_code": -1, "error": "Output file not found"}

# def _json_chunks_from_stdout(stdout: str) -> List[Dict[str, Any]]:
#     """pipeline prints several JSON blobs separated by blank lines; parse the ones that are valid."""
#     chunks = []
#     for part in stdout.split("\n\n"):
#         part = part.strip()
#         if not part:
#             continue
#         try:
#             obj = json.loads(part)
#             chunks.append(obj)
#         except Exception:
#             # ignore non-JSON lines
#             pass
#     return chunks

# def _extract_final(chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
#     """Grab the last chunk with a 'final' key (that’s what pipeline prints at the end)."""
#     final_obj = None
#     for ch in chunks:
#         if isinstance(ch, dict) and "final" in ch:
#             final_obj = ch["final"]
#     return final_obj

# def _shape_final_as_suggestions(final_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
#     suggestions = []
#     # attendance (single)
#     att = final_obj.get("attendance")
#     if att and att.get("applicable") is True:
#         suggestions.append({
#             "item": att.get("item_number"),
#             "description": att.get("item_description"),
#             "confidence": att.get("confidence"),
#             "schedule_fee": att.get("schedule_fee"),
#             "reasoning": att.get("rationale"),
#             "evidence": [{"text": t, "field": "note_facts"} for t in (att.get("citations") or [])]
#         })
#     # procedures (list)
#     for proc in (final_obj.get("procedures") or []):
#         if proc.get("applicable") is True:
#             suggestions.append({
#                 "item": proc.get("item_number"),
#                 "description": proc.get("item_description"),
#                 "confidence": proc.get("confidence"),
#                 "schedule_fee": proc.get("schedule_fee"),
#                 "reasoning": proc.get("rationale"),
#                 "evidence": [{"text": t, "field": "note_facts"} for t in (proc.get("citations") or [])]
#             })
#     return suggestions
def convert_webm_to_wav(webm_path: str) -> str:
    wav_path = webm_path.replace(".webm", ".wav")
    # using ffmpeg to convert webm -> wav
    subprocess.run([
        "ffmpeg", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path
    ], check=True)
    return wav_path

def run_stt_pipeline(tmpdir: str, req: TranscriptionRequest) -> Dict[str, Any]:
    """
    Processes a transcription request with uploaded audio files.
    Converts each audio to mono 16kHz WAV, transcribes using Whisper, 
    and returns the results in a structured format.
    """
    output_path = os.path.join(tmpdir, "transcription.txt")

    cmd = [
        "python",
        os.path.abspath(os.path.join("app", "services", "audio_to_trans.py")),
        "--audio_path", req.attachment,
        "--output", output_path,
        "--model", req.options.stt_model or "tiny.en",
        "--use-faster" if req.options.use_faster_whisper else "",
        "--batched" if req.options.batched_stt else "",
        "--batched-size", req.options.batched_size or "16"]

    env = os.environ.copy()
    process = subprocess.run(cmd, env=env, capture_output=True, text=True)

    print(f"[Main] Running STT command: {' '.join(cmd)}")
    print(f"[Main] STT stdout: {process.stdout}")
    print(f"[Main] STT stderr: {process.stderr}")
    if process.returncode != 0:
        return {"return_code": process.returncode, "error": process.stderr}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            transcription = f.read()
        return {"return_code": 0, "transcription": transcription}
    else:
        return {"return_code": -1, "error": "Output file not found"}
    


# @app.post("/transcribe")
# async def transcribe_audio(req: TranscriptionRequest, file: UploadFile = File(...)):
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
#         tmp_file.write(await file.read())
#         tmp_path = tmp_file.name

#     tmp_path = convert_to_mono_16khz(tmp_path)
#     text = whisper_model.transcribe(tmp_path)
#     os.unlink(tmp_path)
#     return {"transcription": text}

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
        # --- 1️⃣ Save uploaded audio ---
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

        # --- 2️⃣ Transcribe audio ---
        whisper_model = WhisperModelManager("CACHE_DIR")
        model = whisper_model.load_model(speech_model)
        transcription_text = whisper_model.transcribe(tmp_path)
        os.unlink(tmp_path)
        print(f"[Main] Transcription: completed, {len(transcription_text)} chars")
        # --- 3️⃣ Save transcription to temp ---
        transcription_path = os.path.join(tmpdir, "transcription.txt")
        with open(transcription_path, "w", encoding="utf-8") as f:
            f.write(transcription_text)
        # print(f"[Main] Transcription saved to: {transcription_path}")
        # --- 4️⃣ Load session JSON and extract template ---
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
        # --- 5️⃣ Save default prompt file ---
        prompt_temp_path = Path(__file__).parent / "note_structuring_prompt.txt"
        #  = os.path.join(tmpdir, "prompt.txt")
        # shutil.copy(default_prompt, prompt_temp_path)
        print(f"[Main] Prompt file: {prompt_temp_path}")
        # --- 6️⃣ Run LLM pipeline ---
        # structured_notes = run_llm_pipeline(
        #     tmpdir=tmpdir,
        #     req=NoteProcessingRequest(
        #         transcription_path=transcription_path,
        #         prompt_file=prompt_temp_path,
        #         template_file=template_path,
        #         options=Options(llm_model=llm_model)
        #     )
        # )

        ollama_processor = OllamaProcessor(
        model=llm_model
        )

        # 🧩 Process transcription with prompt + template
        print(f"[LLM Pipeline] Generating structured notes using Ollama...")
        structured_notes = ollama_processor.process(
            transcription_text,
            prompt_path=prompt_temp_path,
            template_path=template_path
        )
        
        print(f"[Main] LLM processing completed.", structured_notes)
        # # 💾 Save structured notes to JSON file
        # output_path = Path(output_file)
        # output_path.parent.mkdir(parents=True, exist_ok=True)
        # output_path.write_text(
        #     json.dumps(structured_notes, ensure_ascii=False, indent=2),
        #     encoding="utf-8"
        # )

        # print(f"[LLM Pipeline] Structured notes saved to: {output_path}")

        # if structured_notes.get("return_code") != 0:
        #     print("[Error] LLM pipeline failed:", structured_notes.get("error"))
        #     raise HTTPException(status_code=500, detail=structured_notes.get("error", "LLM pipeline failed."))
        
        # --- 7️⃣ Update session JSON with new content ---
        print("Updating session JSON with new structured notes...")
        session_file = notes_dir / f"{session_id}.json"
        if session_file.exists():
            print("Trying to open session file:", session_file)
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Replace the content object
            session_data["content"] = structured_notes= structured_notes
            print("Replaced content in session_data.")
            # Save back to the same file
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        print(f"[Main] Session {session_id} updated.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str("ohno"))

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


import torch
import numpy as np
from queue import Queue
from datetime import datetime, timedelta
from time import sleep
import speech_recognition as sr
from model_manager import WhisperModelManager
from file_utils import convert_to_mono_16khz
import soundfile as sf
import tempfile
import os

# ---------------- Real-time STT ----------------
CACHE_DIR = "CACHE_DIR"      # Path to cache Whisper models
MODEL_NAME = "small.en"     # Change as needed
RECORD_TIMEOUT = 5           # seconds per phrase
PHRASE_TIMEOUT = 10          # max seconds to keep appending audio
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ----------------------------
# Setup
# ----------------------------
def real_time_stt(model_name=MODEL_NAME):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # adjust if mic is too sensitive
    recognizer.dynamic_energy_threshold = False

    mic = sr.Microphone(sample_rate=16000)
    data_queue = Queue()
    transcription = [""]

    # Load model
    audio_model = WhisperModelManager(CACHE_DIR, use_faster=True).load_model(MODEL_NAME, batched_model=False)

    # ----------------------------
    # Callback for background recording
    # ----------------------------
    def record_callback(_, audio: sr.AudioData):
        data_queue.put(audio.get_raw_data())

    # Adjust ambient noise
    with mic as source:
        print("[INFO] Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    # Start background listening
    recognizer.listen_in_background(mic, record_callback, phrase_time_limit=RECORD_TIMEOUT)
    print("[INFO] Listening in background...")

    # ----------------------------
    # Real-time transcription loop
    # ----------------------------
    phrase_bytes = b""
    phrase_time = datetime.utcnow()

    try:
        while True:
            now = datetime.utcnow()

            # Check if there is new audio
            if not data_queue.empty():
                audio_chunk = b"".join(list(data_queue.queue))
                data_queue.queue.clear()
                phrase_bytes += audio_chunk

                # Check if phrase timeout exceeded
                if (now - phrase_time).total_seconds() > PHRASE_TIMEOUT:
                    phrase_complete = True
                    phrase_time = now
                else:
                    phrase_complete = False

                # Convert bytes to float32 numpy array
                audio_np = np.frombuffer(phrase_bytes, dtype=np.int16).astype(np.float32) / 32768

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    sf.write(tmp_path, audio_np, 16000)
                    # Convert to mono 16kHz (just in case)
                    tmp_path = convert_to_mono_16khz(tmp_path)

                # Transcribe
                segments, info = audio_model.transcribe(tmp_path)
                text = " ".join([seg.text for seg in segments]).strip()
                if phrase_complete:
                    transcription.append(text)
                    phrase_bytes = b""  # reset after phrase complete
                else:
                    transcription[-1] = text

                # Display transcription
                os.system("cls" if os.name == "nt" else "clear")
                for line in transcription:
                    print(line)
                print("", end="", flush=True)

            else:
                sleep(0.25)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping transcription...")
        print("\nFinal transcription:")
        for line in transcription:
            print(line)

# Example usage
if __name__ == "__main__":
    real_time_stt(model_name="tiny.en")
    print("\nFinal Transcript:\n")

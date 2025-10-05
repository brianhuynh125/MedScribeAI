# services/file_utils.py
import tempfile
import os
from pydub import AudioSegment  

def save_upload_tmp(file_bytes: bytes, suffix=".wav") -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name

def cleanup_file(file_path: str):
    if os.path.exists(file_path):
        os.unlink(file_path)

def convert_to_mono_16khz(audio_path: str, output_path: str = None) -> str:
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    if not output_path:
        output_path = audio_path.replace(".wav", "_mono.wav")
    audio.export(output_path, format="wav")
    return output_path
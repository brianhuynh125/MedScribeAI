# stt_whisper_service.py
import whisper
from pydub import AudioSegment
import os

def convert_to_mono_16khz(audio_path: str, output_path: str = None) -> str:
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    if not output_path:
        output_path = audio_path.replace(".wav", "_mono.wav")
    audio.export(output_path, format="wav")
    return output_path

class WhisperSTT:
    def __init__(self, model_name: str = "tiny.en", device: str = "cpu"):
        """
        Load Whisper model
        model_name: tiny/base/small/medium/large/turbo or their .en variants
        device: "cpu" or "cuda"
        """
        self.model = whisper.load_model(model_name, device=device)

    def transcribe(self, audio_path: str, language: str = None, task: str = "transcribe") -> str:
        """
        Transcribe audio file
        language: ISO or name (optional)
        task: "transcribe" or "translate"
        """
        # Convert to mono 16kHz for safety
        mono_path = convert_to_mono_16khz(audio_path)
        
        result = self.model.transcribe(mono_path, language=language, task=task)
        return result["text"]

# Example usage
if __name__ == "__main__":
    stt = WhisperSTT("tiny.en")  # smallest, fastest
    text = stt.transcribe("example_audio.wav")
    print(text)

# services/model_manager.py
import os
# from nemo.collections.asr.models import ASRModel
# from nemo.collections.speechlm2.models import SALM
# Inside app/services/model_manager.py
from app.services.file_utils import convert_to_mono_16khz

class NeMoModelManager:
    def __init__(self, base_dir="models_cache"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.parakeet_path = os.path.join(self.base_dir, "parakeet_model.nemo")
        self.canary_path = os.path.join(self.base_dir, "canary_qwen.nemo")

        self._parakeet_model = None
        self._canary_model = None

    # ---------------- Parakeet TFT ----------------
    def load_parakeet(self):
        if self._parakeet_model:
            return self._parakeet_model

        if os.path.exists(self.parakeet_path):
            print("[ModelManager] Restoring Parakeet from .nemo file...")
            self._parakeet_model = ASRModel.restore_from(self.parakeet_path)
        else:
            print("[ModelManager] Downloading Parakeet from HF and saving locally...")
            self._parakeet_model = ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
            self._parakeet_model.save_to(self.parakeet_path)
        return self._parakeet_model

    # ---------------- Canary Qwen ----------------
    def load_canary(self):
        if self._canary_model:
            return self._canary_model

        if os.path.exists(self.canary_path):
            print("[ModelManager] Restoring Canary Qwen from .nemo file...")
            self._canary_model = SALM.restore_from(self.canary_path)
        else:
            print("[ModelManager] Downloading Canary Qwen from HF and saving locally...")
            self._canary_model = SALM.from_pretrained("nvidia/canary-qwen-2.5b")
            self._canary_model.save_to(self.canary_path)
        return self._canary_model

import os
import torch
# import whisper
from faster_whisper import WhisperModel, BatchedInferencePipeline

class WhisperModelManager:
    def __init__(self, model_dir=None, use_faster=True):
        """
        Manage Whisper model lifecycle, device allocation, and inference modes.
        """
        self.model_dir = model_dir or os.path.expanduser("~/.cache/whisper_models")
        os.makedirs(self.model_dir, exist_ok=True)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[WhisperModelManager] Using device: {self.device}")

        self.models = {}
        self.batched_models = {}
        self.use_faster = use_faster

    def load_model(self, model_name=None, compute_type=None, batched_model=False):
        """
        Loads Whisper model with caching and device awareness.
        - model_name: str, name of the model (tiny, base, small, medium, large, turbo, etc.)
        - compute_type: 'float16', 'int8', etc. (only for faster-whisper)
        """
        # Set default models based on device
        if not model_name:
            model_name = "medium.en" if self.device == "cuda" else "tiny.en"

        if self.use_faster:
            compute_type = compute_type or ("float16" if self.device == "cuda" else "int8")
            print(f"[WhisperModelManager] Loading faster-whisper model {model_name} ({compute_type}) on {self.device}")
            model = WhisperModel(model_name, device=self.device, compute_type=compute_type, download_root=self.model_dir)

            # Wrap in batched inference if requested
            if batched_model:
                print(f"[WhisperModelManager] Wrapping model {model_name} in BatchedInferencePipeline...")
                model = BatchedInferencePipeline(model)

                self.batched_models["batched_whisper"] = model
                print("[WhisperModelManager] Batched Model loaded successfully.")
                return model
        # else:
        #     print(f"[WhisperModelManager] Loading OpenAI Whisper model {model_name} on {self.device}")
        #     model = whisper.load_model(model_name, device=self.device)
        self.models["whisper"] = model
        print("[WhisperModelManager] Model loaded successfully.")
        return model
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe a single audio file using the loaded model.
        """
        if "whisper" not in self.models:
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        model = self.models["whisper"]
        mono_path = convert_to_mono_16khz(audio_path)
        print(f"[WhisperModelManager] Transcribing: {mono_path}")

        if self.use_faster:
            # Faster-whisper supports both direct and batched modes automatically
            segments, info = model.transcribe(mono_path, log_progress=True)
            text = " ".join([seg.text for seg in segments])
        else:
            result = model.transcribe(mono_path)
            text = result["text"]

        return text
    
    def batched_transcribe(self, audio_path, batched_size: int = 16) -> dict:
        """
        Batched transcription on a single audio file.
        """
        if "batched_whisper" not in self.batched_models:
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        model = self.batched_models["batched_whisper"]
        results = {}
        print(f"[WhisperModelManager] Starting batched transcription")

        mono_path = convert_to_mono_16khz(audio_path)
        if self.use_faster:
            segments, info = model.transcribe(mono_path, batch_size = batched_size, log_progress = True)
            text = " ".join([seg.text for seg in segments])
        else:
            result = model.transcribe(mono_path)
            text = result["text"]

        return text

class OllamaModelManager:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.models = {}

    def load_model(self, model_name):
        if model_name in self.models:
            return self.models[model_name]
        print(f"[OllamaModelManager] Loading Ollama model: {model_name}")
        # Here you would implement the actual loading logic, e.g., checking if the model is available
        self.models[model_name] = model_name  # Placeholder for actual model object
        return self.models[model_name]
    

if __name__ == "__main__":
    mgr = WhisperModelManager(use_faster=True)
    model = mgr.load_model("tiny.en", batched_model=True)  # set to True if you want batched pipeline
    text = mgr.batched_transcribe("2086-149220-0033.wav")
    print("\nTranscription result:\n", text)
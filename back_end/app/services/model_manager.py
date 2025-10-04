# services/model_manager.py
import os
from nemo.collections.asr.models import ASRModel
from nemo.collections.speechlm2.models import SALM

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
import whisper
from faster_whisper import WhisperModel

class WhisperModelManager:
    def __init__(self, model_dir=None, use_faster=True):
        self.model_dir = model_dir or os.path.expanduser("~/.cache/whisper_models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[WhisperModelManager] Using device: {self.device}")
        self.models = {}
        self.use_faster = use_faster

    def load_model(self, model_name=None, compute_type="float16"):
        """
        Loads Whisper model with caching and device awareness.
        - model_name: str, name of the model (tiny, base, small, medium, large, turbo, etc.)
        - compute_type: 'float16', 'int8', etc. (only for faster-whisper)
        """
        # Set default models based on device
        if not model_name:
            model_name = "medium.en" if self.device == "cuda" else "tiny.en"

        if self.use_faster:
            compute_type = "float16" if self.device == "cuda" else "int8"
            print(f"[WhisperModelManager] Loading faster-whisper model {model_name} on {self.device}")
            model = WhisperModel(model_name, device=self.device, compute_type=compute_type)
        else:
            print(f"[WhisperModelManager] Loading OpenAI Whisper model {model_name} on {self.device}")
            model = whisper.load_model(model_name, device=self.device)

        print("loading completed")
        self.models["whisper"] = model
        return model

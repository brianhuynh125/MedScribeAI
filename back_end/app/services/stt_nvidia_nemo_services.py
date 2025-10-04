# import os
# from file_utils import cleanup_file
# import nemo.collections.asr as nemo_asr
# from nemo.collections.speechlm2.models import SALM
# import torch

# # ---------------- Local Parakeet TFT ----------------
# _parakeet_model = None #Default

# def load_parakeet_model():
#     global _parakeet_model
#     if _parakeet_model is None:
#         print("Loading Parakeet TFT 0.6B V2...")
#         _parakeet_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
#     return _parakeet_model

# def transcribe_parakeet(file_path: str, timestamps=False):
#     model = load_parakeet_model()
#     output = model.transcribe([file_path], timestamps=timestamps)
#     text = output[0].text
#     time_info = output[0].timestamp if timestamps else None
#     return text, time_info

# # ---------------- Local Canary Qwen 2.5B ----------------
# _canary_model = None

# def load_canary_model():
#     global _canary_model
#     if _canary_model is None:
#         print("Loading Canary Qwen 2.5B...")
#         _canary_model = SALM.from_pretrained('nvidia/canary-qwen-2.5b')
#     return _canary_model

# def transcribe_canary(file_path: str):
#     """
#     ASR mode transcription using Canary Qwen 2.5B.
#     """
#     model = load_canary_model()
#     prompt = "Transcribe the following:"
#     prompts = [
#         [{"role": "user", "content": f"{prompt} {model.audio_locator_tag}", "audio": [file_path]}]
#     ]
#     answer_ids = model.generate(prompts=prompts, max_new_tokens=1024)
#     text = model.tokenizer.ids_to_text(answer_ids[0].cpu())
#     return text


# if __name__ == "__main__":
#     _parakeet_model = load_parakeet_model()
#     ret = transcribe_parakeet("/Users/huynhnguyengiakhang/Documents/GitHub/MedScribeAI/2086-149220-0033.wav")
#     print(ret)
    



# services/stt_service.py
from model_manager import *

# ---------------- Parakeet TFT ----------------
def transcribe_parakeet(file_path: str, timestamps=False):
    """
    Transcribe audio using Parakeet TFT 0.6B V2.
    Supports timestamps.
    """
    model = manager.load_parakeet()
    output = model.transcribe([file_path], timestamps=timestamps)
    text = output[0].text
    time_info = output[0].timestamp if timestamps else None
    return text, time_info

# ---------------- Canary Qwen ----------------
def transcribe_canary(file_path: str, max_tokens=128):
    """
    Transcribe audio using Canary Qwen 2.5B (ASR mode).
    max_tokens controls output length; split audio if needed for long files.
    """
    model = manager.load_canary()
    prompt = "Transcribe the following:"
    prompts = [
        [{"role": "user", "content": f"{prompt} {model.audio_locator_tag}", "audio": [file_path]}]
    ]
    answer_ids = model.generate(prompts=prompts, max_new_tokens=max_tokens)
    text = model.tokenizer.ids_to_text(answer_ids[0].cpu())
    return text

if __name__ == "__main__":
    # Initialize manager with desired folder
    manager = ModelManager()
    from pydub import AudioSegment

    def convert_to_mono_16khz(input_path, output_path=None):
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        if not output_path:
            output_path = input_path.replace(".wav", "_mono.wav")
        audio.export(output_path, format="wav")
        return output_path

    # Usage
    mono_file = convert_to_mono_16khz("/Users/huynhnguyengiakhang/Documents/GitHub/MedScribeAI/I Spent 500 to UPGRADE MY SUBSCRIBERS FC 26 Account! 4 - Danny Aarons.wav")

    for i, y in transcribe_parakeet(mono_file, timestamps= True):
        print("Time: ",y)
        print("Text: ",i)
        print("\n")
        
    

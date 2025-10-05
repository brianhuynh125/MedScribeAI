#!/usr/bin/env python3
import argparse
from pathlib import Path
from app.services.file_utils import convert_to_mono_16khz
from app.services.model_manager import WhisperModelManager


def run_stt_pipeline(
    audio_path: str,
    output_file: str,
    model_name: str = None,
    use_faster: bool = True,
    batched: bool = False,
    batched_size: int = 16,
):
    """
    Speech-to-Text (STT) pipeline:
    - Converts input audio to mono 16kHz WAV
    - Transcribes using Whisper (faster-whisper or openai-whisper)
    - Saves transcription to output file
    - Returns transcription text
    """
    # 1️⃣ Preprocess the audio (ensure correct format)
    audio_path = convert_to_mono_16khz(audio_path)

    # 2️⃣ Initialize Whisper model
    stt_manager = WhisperModelManager(model_dir="CACHE_DIR")
    stt_model = stt_manager.load_model(
        model_name=model_name,
        batched_model=batched,
        use_faster=use_faster
    )

    # 3️⃣ Transcribe
    engine_name = "faster-whisper" if use_faster else "openai-whisper"
    print(f"[STT Pipeline] Transcribing using {engine_name} (batched={batched}, model={model_name})")

    if batched:
        transcription = stt_manager.batched_transcribe(audio_path, batched_size=batched_size)
    else:
        transcription = stt_manager.transcribe(audio_path)

    # 4️⃣ Save output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcription, encoding="utf-8")

    print(f"[STT Pipeline] Transcription saved to: {output_path}")
    return transcription


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Speech-to-Text (STT) Transcription Pipeline")

    parser.add_argument(
        "--audio_path",
        required=True,
        help="Path to the audio file to transcribe (e.g. .wav, .mp3)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to save the transcription output (text file)"
    )
    parser.add_argument(
        "--model",
        default="tiny.en",
        help="Whisper model name (default: tiny.en)"
    )
    parser.add_argument(
        "--use-faster",
        action="store_true",
        help="Use faster-whisper instead of vanilla whisper"
    )
    parser.add_argument(
        "--batched",
        action="store_true",
        help="Use batched transcription mode"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for batched mode (default: 16)"
    )

    args = parser.parse_args()

    # 5️⃣ Run STT pipeline
    run_stt_pipeline(
        audio_path=args.audio_path,
        output_file=args.output,
        model_name=args.model,
        use_faster=args.use_faster,
        batched=args.batched,
        batched_size=args.batch_size,
    )

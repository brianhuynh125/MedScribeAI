#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from llm_ollama_services import OllamaProcessor


def run_llm_pipeline(
    transcription: str,
    prompt_path: str,
    template_path: str,
    output_file: str,
    model_name: str = None,
    temperature: float = 0.0,
):
    """
    Pipeline: Transcription text + template -> Ollama LLM -> Structured JSON output
    """
    print(f"[LLM Pipeline] Using model: {model_name} | Temperature: {temperature}")

    # 🧠 Initialize Ollama processor
    ollama_processor = OllamaProcessor(
        temperature=temperature,
        model=model_name
    )

    # 🧩 Process transcription with prompt + template
    print(f"[LLM Pipeline] Generating structured notes using Ollama...")
    structured_notes = ollama_processor.process(
        transcription,
        prompt_path=prompt_path,
        template_path=template_path
    )

    # 💾 Save structured notes to JSON file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(structured_notes, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[LLM Pipeline] Structured notes saved to: {output_path}")
    return structured_notes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Structured Notes Pipeline")

    parser.add_argument(
        "--transcription_path",
        required=True,
        help="Path to the transcription file (plain text)"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Path to prompt template with placeholders like <<TRANSCRIPTION>>"
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Path to template JSON file for note extraction (placeholder <<TEMPLATE>>)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to save the structured JSON output"
    )
    parser.add_argument(
        "--model",
        default="qwen3:4b-instruct",
        help="LLM model name for Ollama (default: qwen3:4b-instruct)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for LLM (default: 0.0)"
    )

    args = parser.parse_args()

    # 🧾 Load transcription text
    transcription_text = Path(args.transcription_path).read_text(encoding="utf-8")

    # 🚀 Run the pipeline
    run_llm_pipeline(
        transcription=transcription_text,
        prompt_path=args.prompt,
        template_path=args.template,
        output_file=args.output,
        model_name=args.model,
        temperature=args.temperature,
    )

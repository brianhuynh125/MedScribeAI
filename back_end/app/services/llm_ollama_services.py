import os, json, argparse, requests, sys
from pathlib import Path

DEF_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEF_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b-instruct")

class OllamaProcessor:
    def __init__(self, model: str = DEF_MODEL, url: str = DEF_URL, temperature: float = 0.0):
        self.url = url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen3:4b-instruct")
        self.temperature = temperature

    def load_prompt(
        self,
        prompt_path: str | Path,
        transcription: str,
        template_path: str | Path
    ) -> str:
        """
        Load prompt text and replace placeholders with transcription and template JSON.
        """
        try:
            # Read prompt
            prompt_text = Path(prompt_path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"[OllamaProcessor] Failed to read prompt file: {e}")
            raise

        try:
            # Read template JSON
            template_json = Path(template_path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"[OllamaProcessor] Failed to read template file: {e}")
            raise

        # Replace placeholders
        prompt_text = prompt_text.replace("<<TRANSCRIPTION>>", transcription)
        prompt_text = prompt_text.replace("<<TEMPLATE>>", template_json)

        return prompt_text

    def generate(self, prompt: str) -> dict:
        """Call Ollama locally with JSON output enforced."""
        try:
            resp = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "options": {"temperature": self.temperature},
                    "stream": False
                },
                timeout=120
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[OllamaProcessor] Request failed: {e}")
            return {}

        text = resp.json().get("response", "").strip()

        # Try to extract JSON substring if the response is messy
        if not text.startswith("{"):
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e != -1 and e > s:
                text = text[s:e+1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print("[OllamaProcessor] ⚠️ Model output not valid JSON, returning raw text.")
            return text

    def process(
        self,
        transcription: str,
        prompt_path: str | Path = "note_structuring_prompt.txt",
        template_path: str | Path = "note_template.json"
    ) -> dict:
        """
        Convenience wrapper — load prompt + template, insert transcription, and query model.
        """
        prompt = self.load_prompt(prompt_path, transcription, template_path)
        return self.generate(prompt)

    

if __name__ == "__main__":
    example_transcript = Path("data/example_transcript.txt").read_text()
    processor = OllamaProcessor()
    output = processor.process(example_transcript, "note_structuring_prompt.txt")
    print(json.dumps(output, indent=2))
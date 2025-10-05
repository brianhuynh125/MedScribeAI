export type Models = {
  speechToText: "faster-whisper tiny.en" | "faster-whisper small.en";
  llm: "qwen3:4b-instruct" | "llama3.1:4b";
};

export const DEFAULT_MODELS: Models = {
  speechToText: "faster-whisper tiny.en",
  llm: "qwen3:4b-instruct",
};
let currentModels: Models = DEFAULT_MODELS;

const KEY_BASE = "medscribe.fastapi.base";
const KEY_MODELS = "medscribe.models";

export function getFastapiBase(): string | null {
  return localStorage.getItem(KEY_BASE);
}
export function setFastapiBase(url: string) {
  localStorage.setItem(KEY_BASE, url);
}

export function getModels(): Models {
  try {
    const saved = localStorage.getItem(KEY_MODELS);
    if (saved) return JSON.parse(saved) as Models;
  } catch {}
  return currentModels;
}
export function saveModels(models: Models) {
  localStorage.setItem(KEY_MODELS, JSON.stringify(models));
  currentModels = models;
  console.log("Saved models:", models);
}

// export function buildUrl(path: string): string | null {
//   const base = getFastapiBase();
//   if (!base) return null;
//   return `${base.replace(/\/$/, "")}${path.startsWith("/") ? path : "/" + path}`;
// }

export function buildUrl(path: string): string {
  // replace with your backend URL
  const BASE_URL = "http://127.0.0.1:8000";
  return `${BASE_URL}${path}`;
}

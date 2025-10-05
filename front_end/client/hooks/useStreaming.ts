import { useCallback, useRef, useState } from "react";

export interface StreamOptions {
  url: string; // absolute or relative FastAPI endpoint
  method?: "GET" | "POST";
  headers?: Record<string, string>;
  body?: any; // JSON-serializable or undefined
}

export function useStreaming() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const start = useCallback(async (opts: StreamOptions, onChunk: (text: string) => void) => {
    if (!opts?.url) {
      setError("Missing streaming URL");
      return;
    }
    setError(null);
    setIsStreaming(true);
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    try {
      const init: RequestInit = {
        method: opts.method ?? (opts.body ? "POST" : "GET"),
        headers: {
          "Accept": "text/plain, text/event-stream, application/json",
          ...(opts.body ? { "Content-Type": "application/json" } : {}),
          ...(opts.headers ?? {}),
        },
        signal: controller.signal,
      };
      if (opts.body !== undefined) {
        init.body = typeof opts.body === "string" ? opts.body : JSON.stringify(opts.body);
      }
      const res = await fetch(opts.url, init);
      if (!res.ok || !res.body) {
        throw new Error(`Request failed: ${res.status} ${res.statusText}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        if (chunk) onChunk(chunk);
      }
    } catch (err: any) {
      if (err?.name !== "AbortError") {
        setError(err?.message ?? "Streaming error");
      }
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const stop = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setIsStreaming(false);
  }, []);

  return { isStreaming, error, start, stop };
}

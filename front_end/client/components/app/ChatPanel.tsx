import { useMemo, useRef, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useStreaming } from "@/hooks/useStreaming";
import { buildUrl, getModels } from "@/lib/fastapi";
import { Session } from "@/lib/sessions";
import { Checkbox } from "@/components/ui/checkbox";

export interface ChatPanelProps {
  open: boolean;
  onClose: () => void;
  sessions: Session[];
  activeId: string | null;
  onAppendToActive: (text: string) => void;
}

type Msg = { role: "user" | "assistant"; content: string };

export default function ChatPanel({ open, onClose, sessions, activeId }: ChatPanelProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>(activeId ? [activeId] : []);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const { isStreaming, start, stop } = useStreaming();

  const selected = useMemo(() => {
    if (selectedIds.length > 0) return sessions.filter((s) => selectedIds.includes(s.id));
    const fallback = sessions.find((s) => s.id === activeId);
    return fallback ? [fallback] : [];
  }, [sessions, selectedIds, activeId]);

  // auto-scroll when messages array changes
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const toggle = (id: string) => setSelectedIds((arr) => (arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id]));

  const send = async () => {
    const text = input.trim();
    if (!text) return;
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setInput("");
    const url = buildUrl("/chat-stream");
    if (!url) return;
    const m = getModels();
    const payload = {
      sessionIds: selected.map((s) => s.id),
      notes: selected.map((s) => ({ id: s.id, title: s.title, content: s.content })),
      messages: [...messages, { role: "user", content: text }],
      llm_model: m.llm,
    };
    const index = messages.length + 1; // assistant index
    await start({ url, method: "POST", body: payload }, (chunk) => {
      setMessages((prev) => {
        const next = [...prev];
        next[index] = { role: "assistant", content: (next[index]?.content ?? "") + chunk };
        return next;
      });
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    });
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  return (
    <div className={`fixed right-0 top-0 z-40 h-full w-[460px] transform border-l bg-background p-4 shadow-xl transition-transform ${open ? "translate-x-0" : "translate-x-full"}`}>
      <div className="flex items-center justify-between pb-2">
        <div className="font-semibold">Insight AI</div>
        <button className="text-sm text-muted-foreground" onClick={onClose}>Close</button>
      </div>
      <div className="flex h-[calc(100%-2.5rem)] flex-col space-y-3">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Select sessions to include</label>
          <div className="max-h-32 overflow-y-auto rounded-md border p-2">
            {sessions.map((s) => (
              <label key={s.id} className="flex items-center gap-2 py-1">
                <Checkbox checked={selectedIds.includes(s.id)} onCheckedChange={() => toggle(s.id)} />
                <span className="text-sm line-clamp-1">{s.title || "Untitled"}</span>
              </label>
            ))}
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto rounded-md border p-3 space-y-3">
          {messages.length === 0 ? (
            <div className="text-sm text-muted-foreground">Start a conversation. Shift+Enter for newline.</div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "ml-auto bg-primary text-primary-foreground" : "mr-auto bg-secondary"}`}>
                {m.content}
              </div>
            ))
          )}
        </div>

        <div className="flex items-end gap-2">
          <Textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKeyDown} placeholder="Type your question..." className="min-h-[44px]" />
          <Button onClick={send} disabled={isStreaming || !input.trim()}>Send</Button>
          {isStreaming ? <Button variant="outline" onClick={stop}>Stop</Button> : null}
        </div>
      </div>
    </div>
  );
}

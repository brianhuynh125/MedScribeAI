import { useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/app/Sidebar";
import SessionView from "@/components/app/SessionView";
import TopBar from "@/components/app/TopBar";
import { useStreaming } from "@/hooks/useStreaming";
import { buildUrl, getModels } from "@/lib/fastapi";
import { loadSessions, saveSessions, renameSession, Session, deleteSession } from "@/lib/sessions";
import {
  getDefaultTemplate,
  saveDefaultTemplate,
  materializeTemplate,
  applyTemplatePreserve,
} from "@/lib/templates";
import TemplateModal from "@/components/app/TemplateModal";
import ChatPanel from "@/components/app/ChatPanel";
import { Button } from "@/components/ui/button";
import { textToJson, jsonToText } from "@/lib/templates";
import { saveModels, Models} from "@/lib/fastapi";

export default function Index() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");

  const [templateOpen, setTemplateOpen] = useState(false);
  const [insightsOpen, setInsightsOpen] = useState(false);

  const { isStreaming, error, start, stop } = useStreaming();
  const [streamLog, setStreamLog] = useState("");

  const [models, setModels] = useState(() => getModels());
  // --- Load sessions once on mount ---
  useEffect(() => {
    async function fetchSessions() {
      try {
        const data = await loadSessions();
        setSessions(data);
        setActiveId(data[0]?.id ?? null);
      } catch (err) {
        console.error("Failed to load sessions:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSessions();
  }, []);

  // --- Persist sessions whenever they change ---
  useEffect(() => {
    if (!loading) {
      console.log("Triggering saveSessions with:", sessions);
      async function persist() {
        try {
          await saveSessions(sessions);
        } catch (err) {
          console.error("[saveSessions] Failed:", err);
        }
      }
      persist();
    }
  }, [sessions, loading]);

  // --- Active session ---
  const active = useMemo(() => sessions.find((s) => s.id === activeId) ?? null, [sessions, activeId]);

  // --- Create session ---
  const createSession = () => {
    const defaultTemplate = getDefaultTemplate();
    const contentJson = textToJson(materializeTemplate(defaultTemplate), defaultTemplate);

    const s: Session = {
    id: crypto.randomUUID(),
    title: "Untitled session",
    content: contentJson, // JSON
    template: defaultTemplate, // added template
    createdAt: Date.now(),
  };


    setSessions((arr) => [s, ...arr]);
    setActiveId(s.id);
  };

  // --- Delete a session ---
  const deleteSessionById = async (id: string) => {
    setSessions((arr) => arr.filter((s) => s.id !== id));
    setActiveId((prev) => {
      if (prev !== id) return prev;
      const remaining = sessions.filter((s) => s.id !== id);
      return remaining[0]?.id ?? null;
    });

    try {
      await deleteSession(id);
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  // --- Rename session ---
  const onRename = (id: string, title: string) => {
    setSessions((arr) => renameSession(arr, id, title));
  };

  // --- Update content ---
  const updateActiveContent = (text: string) => {
    if (!active) return;
    const template = active.template || getDefaultTemplate();
    const contentJson = textToJson(text, template);
    const updated = { ...active, content: contentJson };
    setSessions((arr) => arr.map((s) => (s.id === active.id ? updated : s)));
  };

  // --- Append to active session (JSON-safe) ---
  const appendToActive = (text:string) => {
  if (!active) return;
  const keys = Object.keys(active.content);
  const firstKey = keys[0] ?? "Notes";
  const updatedContent = { ...active.content, [firstKey]: (active.content[firstKey] ?? "") + text };
  const updated = { ...active, content: updatedContent };
  setSessions(arr => arr.map(s => s.id === active.id ? updated : s));
};


  // --- Streaming & transcription ---
  const handleModelsUpdate = (newModels: Models) => {
  saveModels(newModels);   // updates localStorage
  setModels(newModels);    // updates frontend state
};

  const handleTranscribed = (text: string) => {
    appendToActive("\n" + text);
  };

  useEffect(() => {
    if (error) setStreamLog((t) => t + "\n" + error);
  }, [error]);

  // --- Title editing ---
  const openTitleEdit = () => {
    if (!active) return;
    setEditingTitle(true);
    setTitleDraft(active.title);
  };

  const commitTitle = () => {
    if (!active) return;
    onRename(active.id, titleDraft.trim() || "Untitled session");
    setEditingTitle(false);
  };

  // --- Template modal ---
  const openTemplate = () => setTemplateOpen(true);
  const handleSaveTemplate = (text: string) => saveDefaultTemplate(text);
  const handleApplyTemplate = (newTemplate: string) => {
    if (!active) return;
    const updatedContent = applyTemplatePreserve(active.content, newTemplate);
    const updated = { ...active, content: updatedContent, template: newTemplate };
    setSessions(arr => arr.map(s => s.id === active.id ? updated : s));
    setTemplateOpen(false);
  };

  useEffect(() => {
  console.log("Current active session ID:", activeId);
}, [activeId]);


  // --- Render ---
  if (loading) {
    return <div className="h-screen grid place-content-center text-xl font-semibold">Loading sessions...</div>;
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex h-screen">
        <Sidebar
          sessions={sessions}
          activeId={activeId}
          onSelect={setActiveId}
          onCreate={createSession}
          onDelete={deleteSessionById}
          onRename={onRename}
          onUpdateModels={handleModelsUpdate}
        />
        <main className="flex-1 flex flex-col">
          <div className="flex items-center justify-between border-b px-6 py-4">
            <div className="font-semibold">
              {editingTitle ? (
                <input
                  autoFocus
                  className="rounded-sm bg-transparent outline-none"
                  value={titleDraft}
                  onChange={(e) => setTitleDraft(e.target.value)}
                  onBlur={commitTitle}
                  onKeyDown={(e) => { if (e.key === "Enter") commitTitle(); }}
                />
              ) : (
                <button onClick={openTitleEdit}>{active?.title ?? "No session"}</button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setInsightsOpen(true)}>Insights</Button>
              <TopBar onTranscribed={handleTranscribed} 
              activeSessionId={activeId}/>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            {active ? (
              <SessionView
  value={active.content} // <-- use 'value', not 'content'
  onChange={(jsonContent) => {
    if (!active) return;
    const updated = { ...active, content: jsonContent };
    setSessions((arr) => arr.map((s) => (s.id === active.id ? updated : s)));
  }}
  onAppend={appendToActive}
  onOpenTemplate={openTemplate}
  template={active.template || getDefaultTemplate()}
  activeId={activeId}
/>

            ) : (
              <div className="h-full grid place-content-center">
                <button className="text-primary underline" onClick={createSession}>
                  Create your first session
                </button>
              </div>
            )}
          </div>
          <div className="border-t bg-muted/30 px-6 py-3 text-sm">
            <div className="flex items-center justify-between">
              <div className="font-medium">Stream</div>
              {isStreaming ? <button className="text-primary" onClick={stop}>Stop</button> : null}
            </div>
            <pre className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap text-muted-foreground">{streamLog || "No stream yet"}</pre>
          </div>
        </main>
      </div>
      <TemplateModal
        open={templateOpen}
        initial={getDefaultTemplate()}
        onClose={() => setTemplateOpen(false)}
        onSave={handleSaveTemplate}
        onApply={handleApplyTemplate}
      />
      <ChatPanel
        open={insightsOpen}
        onClose={() => setInsightsOpen(false)}
        sessions={sessions}
        activeId={activeId}
        onAppendToActive={appendToActive}
      />
    </div>
  );
}

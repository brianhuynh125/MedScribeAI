import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { Models, getModels, saveModels, getFastapiBase, setFastapiBase } from "@/lib/fastapi";
import { Plus, Settings, Trash2 } from "lucide-react";
import { Session } from "@/lib/sessions";

export interface SidebarProps {
  sessions: Session[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onUpdateModels?: (m: Models) => Promise<void> | void;
  compact?: boolean;
}

export default function Sidebar({ sessions, activeId, onSelect, onCreate, onDelete, onRename, onUpdateModels, compact }: SidebarProps) {
  const [models, setModels] = useState<Models>(() => getModels());
  const [updating, setUpdating] = useState(false);
  const [baseUrlInput, setBaseUrlInput] = useState<string>(getFastapiBase() ?? "");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [titleDraft, setTitleDraft] = useState<string>("");
  const [hoverId, setHoverId] = useState<string | null>(null);

  const sorted = useMemo(() => sessions.slice().sort((a, b) => b.createdAt - a.createdAt), [sessions]);

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      // Save models locally
      saveModels(models);

      // Call optional callback to propagate models up
      if (onUpdateModels) await onUpdateModels(models);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <aside className={cn("flex h-full w-72 shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground", compact && "w-16")}> 
      <div className="flex items-center justify-between px-4 py-3">
        <div className="font-extrabold tracking-tight text-lg">MedScribe AI</div>
        <Button size="icon" variant="ghost" onClick={onCreate} aria-label="New session">
          <Plus />
        </Button>
      </div>
      <div className="px-3 pb-2 text-xs uppercase text-muted-foreground">Sessions</div>
      <nav className="flex-1 overflow-y-auto px-2 space-y-1">
        {sorted.length === 0 && (
          <div className="text-sm text-muted-foreground px-2 py-3">No sessions yet</div>
        )}
        {sorted.map((s) => (
          <div
            key={s.id}
            onMouseEnter={() => setHoverId(s.id)}
            onMouseLeave={() => setHoverId((id) => (id === s.id ? null : id))}
            onClick={() => onSelect(s.id)}
            className={cn("group flex w-full cursor-pointer items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-accent", activeId === s.id && "bg-accent")}
          >
            {editingId === s.id ? (
              <input
                autoFocus
                value={titleDraft}
                onChange={(e) => setTitleDraft(e.target.value)}
                onBlur={() => { onRename(s.id, titleDraft.trim() || "Untitled session"); setEditingId(null); }}
                onKeyDown={(e) => { if (e.key === "Enter") { (e.target as HTMLInputElement).blur(); } }}
                className="w-full rounded-sm bg-transparent outline-none"
              />
            ) : (
              <span
                className={cn("flex-1 line-clamp-1", hoverId === s.id && activeId === s.id && "underline")}
                onClick={(e) => {
                  if (activeId === s.id && hoverId === s.id) {
                    e.stopPropagation();
                    setEditingId(s.id);
                    setTitleDraft(s.title || "");
                  }
                }}
                title={activeId === s.id ? "Click to edit" : "Click to open"}
              >
                {s.title || "Untitled session"}
              </span>
            )}
            <button className="opacity-0 group-hover:opacity-100" onClick={(e) => { e.stopPropagation(); onDelete(s.id); }} aria-label="Delete">
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </nav>

      <div className="border-t p-3 space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium"><Settings className="h-4 w-4"/> Settings</div>
        <div className="space-y-2">
          <label className="text-xs text-muted-foreground">Speech-to-text model</label>
          <Select value={models.speechToText} onValueChange={(v) => setModels(m => ({ ...m, speechToText: v as Models["speechToText"] }))}>
            <SelectTrigger><SelectValue placeholder="Select model" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="faster-whisper tiny.en">faster-whisper tiny.en</SelectItem>
              <SelectItem value="faster-whisper small.en">faster-whisper small.en</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label className="text-xs text-muted-foreground">LLM model</label>
          <Select value={models.llm} onValueChange={(v) => setModels(m => ({ ...m, llm: v as Models["llm"] }))}>
            <SelectTrigger><SelectValue placeholder="Select model" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="qwen3:4b-instruct">qwen3:4b-instruct</SelectItem>
              <SelectItem value="llama3.1:4b">llama3.1:4b</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {/* <div className="space-y-2">
          <label className="text-xs text-muted-foreground">FastAPI base URL</label>
          <input className="w-full rounded-md border bg-background px-3 py-2 text-sm" placeholder="https://your-fastapi.example.com" value={baseUrlInput} onChange={(e) => setBaseUrlInput(e.target.value)} />
        </div> */}
        <Button className="w-full" onClick={handleUpdate} disabled={updating}>{updating ? "Updating..." : "Update"}</Button>
      </div>
    </aside>
  );
}

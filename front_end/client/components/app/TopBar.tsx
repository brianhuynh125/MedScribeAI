import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Mic } from "lucide-react";
import AudioModal, { SavedFile } from "@/components/app/AudioModal";

export interface TopBarProps {
  onTranscribed: (text: string) => void;
  activeSessionId?: string | null;
}

type Attached = { id: string; name: string; size: number };

export default function TopBar({ onTranscribed, activeSessionId}: TopBarProps) {
  const [attached, setAttached] = useState<Attached[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"upload" | "record">("upload");

  const onSaved = (f: SavedFile) => {
    setAttached((a) => [{ id: crypto.randomUUID(), name: f.name, size: f.size }, ...a]);
  };

  return (
    <div className="flex items-center justify-end gap-3">
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={() => {console.log("Opening AudioModal with session ID:", activeSessionId); setModalMode("upload"); setModalOpen(true); }}>
          <Upload /> Upload/Manage
        </Button>
        <Button onClick={() => { console.log("Opening AudioModal with session ID:", activeSessionId);setModalMode("record"); setModalOpen(true); }}>
          <Mic /> Record
        </Button>
      </div>
      {attached.length > 0 && (
        <div className="flex max-w-[420px] flex-wrap gap-2">
          {attached.map((f) => (
            <span key={f.id} className="inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs">
              {f.name}
            </span>
          ))}
        </div>
      )}

      <AudioModal
        open={modalOpen}
        initialMode={modalMode}
        onClose={() => setModalOpen(false)}
        onSaved={onSaved}
        onTranscribed={onTranscribed}
        activeSessionId={activeSessionId}
      />
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { buildUrl, getModels } from "@/lib/fastapi";
import { loadSessions, Session, saveSessions } from "@/lib/sessions";

export type SavedFile = { name: string; size: number; path: string };

export interface AudioModalProps {
  open: boolean;
  initialMode: "upload" | "record";
  onClose: () => void;
  onSaved?: (file: SavedFile) => void;
  onTranscribed?: (text: string) => void;
  activeSessionId?: string | null;
}

export default function AudioModal({ open, initialMode, onClose, onSaved, onTranscribed, activeSessionId}: AudioModalProps) {
  const [mode, setMode] = useState<typeof initialMode>(initialMode);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  useEffect(() => { setMode(initialMode); }, [initialMode, open]);

  const pickFile = (f: File) => {
    const isWav = /wav/i.test(f.type) || /\.wav$/i.test(f.name);
    if (!isWav) {
      alert("Only .wav files are allowed.");
      return;
    }
    setSelectedFile(f);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) pickFile(f);
    e.currentTarget.value = "";
  };

  const startRec = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mr;
      chunksRef.current = [];
      mr.ondataavailable = (ev) => { if (ev.data.size > 0) chunksRef.current.push(ev.data); };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        chunksRef.current = [];
        const file = new File([blob], `recording-${Date.now()}.webm`, { type: "audio/webm" });
        setSelectedFile(file);
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      setRecording(true);
      setPaused(false);
    } catch (e) {
      console.error(e);
      alert("Microphone access denied");
    }
  };

  const pauseRec = () => { mediaRecorderRef.current?.pause(); setPaused(true); };
  const resumeRec = () => { mediaRecorderRef.current?.resume(); setPaused(false); };
  const stopRec = () => { mediaRecorderRef.current?.stop(); setRecording(false); setPaused(false); };
  const quitRec = () => { try { mediaRecorderRef.current?.stop(); } catch {} setRecording(false); setPaused(false); setSelectedFile(null); };

  const discardFile = () => {
    setSelectedFile(null);
  };

  const downloadFile = () => {
    if (!selectedFile) return;
    const url = URL.createObjectURL(selectedFile);
    const a = document.createElement("a");
    a.href = url;
    a.download = selectedFile.name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    onSaved?.({ name: selectedFile.name, size: selectedFile.size, path: selectedFile.name });
  };

  const transcribe = async () => {
  if (!selectedFile) return;
    if (!activeSessionId) {
  alert("No active session — cannot transcribe.");
  return;
}
  const url = buildUrl("/transcribe_process"); // from your fastapi.ts
  console.log("Opening AudioModal with session ID:", activeSessionId)
  if (!url) { 
    alert("Backend URL not set"); 
    return; 
  }

  const form = new FormData();
  form.append("file", selectedFile);
  form.append("session_id", activeSessionId);
  // Add model param if you have it in your fastapi.ts
  const models = getModels();
  form.append("speech_model", models.speechToText);
  form.append("llm_model", models.llm);

  try {
    const res = await fetch(url, { method: "POST", body: form });
    if (!res.ok) {
      alert("Transcription failed");
      return;
    }
    const updatedSessions = await loadSessions();
    saveSessions(updatedSessions);
  } catch (e: any) {
    console.error("Transcription error:", e);
    alert(`Transcription failed: ${e.message}`);
  }
    };


  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload & Record</DialogTitle>
          <DialogDescription>Download audio locally after saving.</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2 mb-3">
          <Button variant={mode === "upload" ? "default" : "outline"} onClick={() => setMode("upload")}>Upload</Button>
          <Button variant={mode === "record" ? "default" : "outline"} onClick={() => setMode("record")}>Record</Button>
        </div>

        {mode === "upload" ? (
          <div className="space-y-2">
            <input type="file" accept="audio/wav,.wav" onChange={onFileChange} />
          </div>
        ) : (
          <div className="space-y-2">
            {!recording ? (
              <Button onClick={startRec}>Start recording</Button>
            ) : (
              <div className="flex items-center gap-2">
                {paused ? (
                  <Button variant="secondary" onClick={resumeRec}>Resume</Button>
                ) : (
                  <Button variant="secondary" onClick={pauseRec}>Pause</Button>
                )}
                <Button variant="destructive" onClick={stopRec}>Stop</Button>
              </div>
            )}
          </div>
        )}

        {selectedFile && (
          <div className="flex items-center gap-2 mt-2">
            <div className="text-sm truncate">{selectedFile.name}</div>
            <Button variant="destructive" size="sm" onClick={discardFile}>X</Button>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 mt-3">
          <Button variant="outline" onClick={downloadFile} disabled={!selectedFile}>Download</Button>
          <Button onClick={transcribe} disabled={!selectedFile}>Transcribe</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

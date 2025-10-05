import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Copy, Download, Save } from "lucide-react";
import { textToJson, jsonToText } from "@/lib/templates";
import { loadSessions } from "@/lib/sessions";
export interface SessionViewProps {
  value: Record<string, string>;
  template: string;
  onChange: (v: Record<string, string>) => void;
  onAppend?: (v: string) => void;
  onOpenTemplate: () => void;
  activeId?: string | null;
}

export default function SessionView({
  value,
  template,
  onChange,
  onAppend,
  onOpenTemplate,
  activeId,
}: SessionViewProps) {
  const [saved, setSaved] = useState(false);
  const [status, setStatus] = useState("");
  const printRef = useRef<HTMLDivElement | null>(null);

  // Reset saved state
  useEffect(() => {
    if (!saved) return;
    const t = setTimeout(() => setSaved(false), 1200);
    return () => clearTimeout(t);
  }, [saved]);

  // Handlers
  const handleSave = () => {
    setSaved(true);
    setStatus("Saved locally");
  };

  const handleCopy = async () => {
    try {
      const text = jsonToText(value, template);
      await navigator.clipboard.writeText(text);
      setStatus("Copied to clipboard");
    } catch {}
  };

  const downloadDoc = () => {
    const text = jsonToText(value, template);
    const html = `<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><pre>${escapeHtml(
      text
    )}</pre></body></html>`;
    const blob = new Blob([html], { type: "application/msword" });
    triggerDownload(blob, "notes.doc");
  };

  const downloadPdf = () => {
    const text = jsonToText(value, template);
    const w = window.open("", "_blank");
    if (!w) return;
    const html = `<html><head><meta charset='utf-8'><title>Notes</title><style>body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:24px;white-space:pre-wrap}</style></head><body>${escapeHtml(
      text
    ).replace(/\n/g, "<br>")}</body></html>`;
    w.document.write(html);
    w.document.close();
    w.focus();
    w.print();
  };

  // Split template fields
  const fields = template.split("\n").filter(Boolean);

  const handleFieldChange = (field: string, text: string) => {
    onChange({ ...value, [field]: text });
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between gap-2 py-2">
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={handleSave}>
            <Save /> Save changes
          </Button>
          <Button variant="outline" onClick={handleCopy}>
            <Copy /> Copy
          </Button>
          <Button variant="outline" onClick={downloadDoc}>
            <Download /> Download .doc
          </Button>
          <Button variant="outline" onClick={downloadPdf}>
            <Download /> Download .pdf
          </Button>
          <Button variant="outline" onClick={onOpenTemplate}>
            Change template
          </Button>
          <Button
    variant="outline"
    onClick={async () => {
      // Refresh: reload sessions from backend
      const updatedSessions = await loadSessions(); // import from your lib/sessions
      const current = updatedSessions.find(s => s.id === activeId); // activeId must be passed as prop
      if (current) onChange(current.content);
      setStatus("Session refreshed");
    }}
  >
    Refresh
  </Button>

  <Button
    variant="destructive"
    onClick={() => {
      // Clear: reset to default template
      const defaultContent = textToJson(template, template); // empty default
      onChange(defaultContent);
      setStatus("Session cleared");
    }}
  >
    Clear
  </Button>
        </div>
        <div className="text-sm text-muted-foreground">{status}</div>
      </div>

      <div ref={printRef} className="flex-1 overflow-y-auto flex flex-col gap-4">
        {/* Render template fields */}
        {fields.map((field) => (
          <div key={field} className="flex flex-col">
            <label className="font-semibold">{field}</label>
            <textarea
              className="border rounded p-2 resize-none w-full"
              value={value[field] ?? ""}
              onChange={(e) => handleFieldChange(field, e.target.value)}
              rows={3}
              placeholder={`Enter ${field}...`}
            />
          </div>
        ))}

        {/* Render extra fields not in template */}
        {Object.keys(value)
          .filter((f) => !fields.includes(f) && f.trim() !== "")
          .map((field) => (
            <div key={field} className="flex flex-col">
              <label className="font-semibold">{field}</label>
              <textarea
                className="border rounded p-2 resize-none w-full"
                value={value[field]}
                onChange={(e) => handleFieldChange(field, e.target.value)}
                rows={3}
              />
            </div>
          ))}
      </div>
    </div>
  );
}

// Helpers
function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function escapeHtml(text: string) {
  const map: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
    "\n": "\n",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

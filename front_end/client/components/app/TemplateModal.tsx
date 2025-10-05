import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from "react";

export interface TemplateModalProps {
  open: boolean;
  initial: string;
  onClose: () => void;
  onSave: (text: string) => void;
  onApply: (text: string) => void;
}

import { resetDefaultTemplate } from "@/lib/templates";

export default function TemplateModal({ open, initial, onClose, onSave, onApply }: TemplateModalProps) {
  const [text, setText] = useState(initial);
  useEffect(() => setText(initial), [initial]);

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Customize template</DialogTitle>
          <DialogDescription>Each line becomes a section heading in the note.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <Textarea className="h-64 w-full" value={text} onChange={(e) => setText(e.target.value)} />
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs text-muted-foreground">Tip: headings are lines ending with ":" in notes.</div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setText(resetDefaultTemplate())}>Reset to default</Button>
              <Button variant="secondary" onClick={() => onSave(text)}>Save as default</Button>
              <Button onClick={() => onApply(text)}>Apply to notes</Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

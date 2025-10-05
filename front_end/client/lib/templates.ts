const KEY_TEMPLATE_DEFAULT = "medscribe.template.default";

export const DEFAULT_TEMPLATE = [
  "Patient name",
  "Patient sex",
  "Patient age",
  "Subjective",
  "Objective",
  "Assessment",
  "Plan",
].join("\n");

export function getDefaultTemplate(): string {
  const t = localStorage.getItem(KEY_TEMPLATE_DEFAULT);
  return t ?? DEFAULT_TEMPLATE;
}

export function saveDefaultTemplate(text: string) {
  localStorage.setItem(KEY_TEMPLATE_DEFAULT, text);
}

export function resetDefaultTemplate(): string {
  localStorage.setItem(KEY_TEMPLATE_DEFAULT, DEFAULT_TEMPLATE);
  return DEFAULT_TEMPLATE;
}

export function materializeTemplate(text: string): string {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  return lines.map((l) => `${l}:\n`).join("\n");
}

// export function textToJson(text: string, template: string): Record<string, string> {
//   const templateLines = template.split("\n").map((line) => line.replace(":", "").trim());
//   const textLines = text.split("\n");
//   const result: Record<string, string> = {};

//   templateLines.forEach((field, i) => {
//     // remove field name from line if present
//     const line = textLines[i] ?? "";
//     const value = line.replace(/^.*?:/, "").trim();
//     result[field] = value;
//   });

//   return result;
// }

// export function jsonToText(content: Record<string, string>, template: string): string {
//   const templateLines = template.split("\n").map((line) => line.trim());
//   return templateLines
//     .map((field) => `${field}: ${content[field] ?? ""}`)
//     .join("\n");
// }

// jsonToText: Record<string,string> -> string for textarea display
export function jsonToText(json: Record<string, string>, template: string) {
  const lines: string[] = [];
  const fields = template.split("\n").filter(Boolean); // split template by lines

  for (const field of fields) {
    lines.push(`${field}: ${json[field] ?? ""}`);
  }

  // Include any extra fields in json that are not in template
  for (const key of Object.keys(json)) {
    if (!fields.includes(key) && key.trim() !== "") {
      lines.push(`${key}: ${json[key]}`);
    }
  }

  return lines.join("\n");
}


// textToJson: string (textarea) + template -> Record<string,string>
export function textToJson(text: string, template: string): Record<string, string> {
  const json: Record<string, string> = {};
  const lines = text.split("\n");

  for (const line of lines) {
    const [field, ...rest] = line.split(":");
    if (field.trim() !== "") {
      json[field.trim()] = rest.join(":").trim();
    }
  }

  // Ensure all template fields exist
  for (const field of template.split("\n").filter(Boolean)) {
    if (!(field in json)) json[field] = "";
  }

  return json;
}


// applyTemplatePreserve: preserve existing data when template changes
export function applyTemplatePreserve(oldContent: Record<string,string>, newTemplate: string): Record<string,string> {
  const newFields = newTemplate.split("\n");
  const newContent: Record<string,string> = {};
  newFields.forEach(f => {
    if (oldContent[f] !== undefined) {
      newContent[f] = oldContent[f]; // preserve existing notes
    } else {
      newContent[f] = ""; // new field, empty
    }
  });
  return newContent;
}


export type ParsedNotes = { sections: Record<string, string>; extras: string };

export function parseNotes(text: string): ParsedNotes {
  const lines = text.split(/\r?\n/);
  const sections: Record<string, string> = {};
  let current: string | null = null;
  const buf: string[] = [];
  const extrasBuf: string[] = [];
  const flush = () => {
    if (current !== null) {
      sections[current] = buf.join("\n").trim();
    } else if (buf.length) {
      extrasBuf.push(buf.join("\n").trim());
    }
    buf.length = 0;
  };
  for (const raw of lines) {
    const l = raw;
    const m = /^\s*([^:]+):\s*$/.exec(l);
    if (m) {
      flush();
      current = m[1].trim();
      continue;
    }
    buf.push(l);
  }
  flush();
  const extras = extrasBuf.filter(Boolean).join("\n");
  return { sections, extras };
}

export function formatNotes(order: string[], sections: Record<string, string>, extras?: string): string {
  const parts: string[] = [];
  for (const key of order) {
    const body = (sections[key] ?? "").trim();
    parts.push(`${key}:`);
    parts.push(body ? body : "");
    parts.push("");
  }
  if (extras && extras.trim()) {
    parts.push("Additional:");
    parts.push(extras.trim());
    parts.push("");
  }
  return parts.join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n";
}

// export function applyTemplatePreserve(currentText: string, templateText: string): string {
//   const { sections, extras } = parseNotes(currentText);
//   const order = templateText.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
//   const nextSections: Record<string, string> = {};
//   for (const key of order) {
//     nextSections[key] = sections[key] ?? "";
//   }
//   // keep leftover sections that were not in template
//   const leftoverKeys = Object.keys(sections).filter((k) => !order.includes(k));
//   let leftover = extras;
//   for (const k of leftoverKeys) {
//     const v = sections[k];
//     if (v && v.trim()) {
//       leftover = [leftover, `${k}:\n${v}`].filter(Boolean).join("\n\n");
//     }
//   }
//   return formatNotes(order, nextSections, leftover);
// }

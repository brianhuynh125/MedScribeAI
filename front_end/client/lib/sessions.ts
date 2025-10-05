import { buildUrl } from "./fastapi";

export interface Session {
  id: string;
  title: string;
  content: Record<string, string>; // now JSON
  createdAt: number;
  template: string; // add this line
}


export async function loadSessions(): Promise<Session[]> {
  const url = buildUrl("/sessions");
  if (!url) return [];
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as Session[];
  } catch (err) {
    console.error("[loadSessions] Failed to fetch sessions:", err);
    return [];
  }
}

/**
 * Save one or multiple sessions
 */
export async function saveSessions(sessions: Session | Session[]): Promise<void> {
  const url = buildUrl("/sessions");
  console.log("saveSessions URL:", url); // <- add this
  if (!url) return; // if url is falsy, fetch never happens
  try {
    const payload = Array.isArray(sessions) ? sessions : [sessions];
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    console.log("Sessions saved:", payload);
  } catch (err) {
    console.error("[saveSessions] Failed to save sessions:", err);
  }
}



export async function deleteSession(id: string): Promise<void> {
  const url = buildUrl(`/sessions/${id}`);
  if (!url) return;
  try {
    await fetch(url, { method: "DELETE" });
  } catch (err) {
    console.error("[deleteSession] Failed to delete session:", err);
  }
}

export function renameSession(sessions: Session[], id: string, title: string): Session[] {
  return sessions.map((s) => (s.id === id ? { ...s, title } : s));
}

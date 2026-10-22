import { FormEvent, useCallback, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import TurnstileBox, { type TurnstileHandle } from "../components/TurnstileBox";
import { api } from "../lib/api";
import type { ScanResult } from "../types";

const LEVELS = {
  low: { title: "Looks safe", color: "bg-kelp", text: "text-kelp", note: "We found no common scam signals. Stay careful with anything that asks for money or codes." },
  medium: { title: "Be careful", color: "bg-beam", text: "text-[#9A6400]", note: "Some warning signs. Verify the sender through an official channel before acting." },
  high: { title: "Likely a scam or abusive", color: "bg-buoy", text: "text-buoy", note: "Do not reply, tap links or share codes. Block the sender." },
} as const;

export default function Checker() {
  const location = useLocation();
  const [text, setText] = useState<string>((location.state as { text?: string } | null)?.text ?? "");
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const ts = useRef<TurnstileHandle>(null);
  const onToken = useCallback((t: string) => setToken(t), []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(""); setResult(null);
    try { setResult(await api.scan(text, token)); }
    catch (err) { setError((err as Error).message); }
    finally { setBusy(false); ts.current?.reset(); }
  }

  const level = result ? LEVELS[result.level] : null;

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <h1 className="text-3xl font-bold">Scam message checker</h1>
      <p className="mt-2 max-w-xl text-muted">Paste a text you received. We look for scam wording and risky links. Nothing you paste is stored.</p>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="t" className="label">Message to check</label>
          <textarea id="t" rows={6} maxLength={1000} className="field" value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste the message here" />
          <p className="mt-1 text-right text-xs text-muted">{text.length}/1000</p>
        </div>
        <TurnstileBox ref={ts} onToken={onToken} />
        <button className="btn-primary" disabled={busy || !text.trim() || !token}>{busy ? "Checking..." : "Check message"}</button>
      </form>

      {error && <p role="alert" className="mt-6 rounded-lg border border-buoy/40 bg-buoy/10 p-3 font-semibold text-buoy">{error}</p>}

      {result && level && (
        <section className="mt-10" aria-live="polite" aria-label="Result">
          <div className="flex items-end justify-between gap-4">
            <h2 className={`text-3xl font-extrabold ${level.text}`}>{level.title}</h2>
            <p className="font-display text-xl font-bold">Risk {result.score}/100</p>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full bg-ink/10" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={result.score} aria-label="Risk score">
            <div className={`h-full rounded-full ${level.color}`} style={{ width: `${Math.max(result.score, 3)}%` }} />
          </div>
          <p className="mt-3 text-muted">{level.note}</p>

          {result.reasons.length > 0 && (
            <>
              <h3 className="mt-8 text-xl font-bold">Why</h3>
              <ul className="mt-2 space-y-2">
                {result.reasons.map((r) => (
                  <li key={r.code} className="border-l-4 border-buoy pl-3">{r.label}</li>
                ))}
              </ul>
            </>
          )}

          {result.urls.length > 0 && (
            <>
              <h3 className="mt-8 text-xl font-bold">Links in this message</h3>
              <ul className="mt-2 space-y-3">
                {result.urls.map((u) => (
                  <li key={u.url} className="rounded-lg border border-ink/10 bg-white p-3">
                    <p className="break-all font-mono text-sm">{u.url}</p>
                    <p className={`mt-1 text-sm ${u.flags.length ? "font-semibold text-buoy" : "text-muted"}`}>
                      {u.flags.length ? u.flags.join(". ") + "." : "No obvious problems with this link."}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          )}

          {result.advice.length > 0 && (
            <>
              <h3 className="mt-8 text-xl font-bold">What to do</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5">{result.advice.map((a) => <li key={a}>{a}</li>)}</ul>
            </>
          )}
          <p className="mt-8 text-sm text-muted">This is an automated estimate, not a guarantee. When in doubt, contact the organisation through its official website or app.</p>
        </section>
      )}
    </div>
  );
}

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import TurnstileBox, { type TurnstileHandle } from "../components/TurnstileBox";
import { ApiError, api } from "../lib/api";

const CATEGORIES = [
  ["spam", "Spam"], ["scam", "Scam or phishing"], ["harassment", "Harassment"], ["threat", "Threat"], ["other", "Something else"],
];

export default function Recipient() {
  const { token = "" } = useParams();
  const [info, setInfo] = useState<{ to: string; blocked: boolean } | null>(null);
  const [missing, setMissing] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [reported, setReported] = useState(false);
  const [category, setCategory] = useState("spam");
  const [details, setDetails] = useState("");
  const [ts, setTs] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const tsRef = useRef<TurnstileHandle>(null);
  const onToken = useCallback((t: string) => setTs(t), []);

  useEffect(() => {
    api.recipient(token).then(
      (i) => { setInfo(i); setBlocked(i.blocked); },
      (e: ApiError) => e.status === 404 ? setMissing(true) : setError(e.message),
    );
  }, [token]);

  async function block() {
    setBusy(true); setError("");
    try { await api.block(token); setBlocked(true); } catch (e) { setError((e as Error).message); }
    setBusy(false);
  }

  async function report(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError("");
    try { await api.report(token, category, details, ts); setReported(true); setBlocked(true); }
    catch (err) { setError((err as Error).message); tsRef.current?.reset(); }
    setBusy(false);
  }

  if (missing)
    return (
      <div className="mx-auto max-w-xl px-5 py-20">
        <h1 className="text-3xl font-bold">Link not recognised</h1>
        <p className="mt-3 text-muted">This link is invalid or has been removed. If you keep getting unwanted texts, reply STOP to the message.</p>
      </div>
    );

  return (
    <div className="mx-auto max-w-xl px-5 py-12">
      <h1 className="text-3xl font-bold">Stop messages or report abuse</h1>
      <p className="mt-3 text-muted">
        You received a text sent through Texhaven{info ? <> to <strong className="text-ink">{info.to}</strong></> : ""}. The sender cannot see who you are.
      </p>

      {error && <p role="alert" className="mt-4 rounded-lg border border-buoy/40 bg-buoy/10 p-3 font-semibold text-buoy">{error}</p>}

      <section className="mt-8">
        <h2 className="text-xl font-bold">Block this number</h2>
        <p className="mt-1 text-muted">Texhaven will never send to this number again, and any pending message is cancelled.</p>
        {blocked ? (
          <p role="status" className="mt-3 rounded-lg bg-kelp/15 p-3 font-semibold text-kelp">This number is blocked.</p>
        ) : (
          <button className="btn-primary mt-3" onClick={block} disabled={busy || !info}>Block this number</button>
        )}
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold">Report abuse</h2>
        {reported ? (
          <p role="status" className="mt-3 rounded-lg bg-kelp/15 p-3 font-semibold text-kelp">Thank you. Your report was received and the number is blocked.</p>
        ) : (
          <form onSubmit={report} className="mt-3 space-y-4">
            <fieldset>
              <legend className="label">What was it?</legend>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map(([v, l]) => (
                  <label key={v} className={`cursor-pointer rounded-lg border px-3 py-2 text-sm font-semibold ${category === v ? "border-ink bg-ink text-white" : "border-ink/20 bg-white"}`}>
                    <input type="radio" name="cat" value={v} checked={category === v} onChange={() => setCategory(v)} className="sr-only" />
                    {l}
                  </label>
                ))}
              </div>
            </fieldset>
            <div>
              <label htmlFor="d" className="label">Details (optional)</label>
              <textarea id="d" rows={3} maxLength={500} className="field" value={details} onChange={(e) => setDetails(e.target.value)} />
            </div>
            <TurnstileBox ref={tsRef} onToken={onToken} />
            <button className="btn-primary" disabled={busy || !ts}>Send report</button>
          </form>
        )}
      </section>
    </div>
  );
}

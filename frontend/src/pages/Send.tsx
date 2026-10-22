import { FormEvent, useCallback, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import PhoneBubble from "../components/PhoneBubble";
import PhoneField from "../components/PhoneField";
import TurnstileBox, { type TurnstileHandle } from "../components/TurnstileBox";
import { ApiError, api } from "../lib/api";
import { useConfig } from "../lib/config";
import { footerFor, formatMoney, smsInfo } from "../lib/sms";

export default function Send() {
  const { config, error: configError } = useConfig();
  const [params] = useSearchParams();
  const [to, setTo] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const ts = useRef<TurnstileHandle>(null);
  const onToken = useCallback((t: string) => setToken(t), []);

  const footer = config ? footerFor(config.footer_template) : "";
  const info = useMemo(() => smsInfo(body + footer), [body, footer]);
  const overLimit = !!config && info.segments > config.max_segments;
  const price = config ? formatMoney(info.segments * config.price_per_segment_cents, config.currency) : "";
  const canSubmit = !!to && body.trim().length > 0 && !!token && !overLimit && !busy;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!to) return;
    setBusy(true); setError(null);
    try {
      const msg = await api.createMessage(to, body, token);
      window.location.assign(msg.checkout_url!);
    } catch (err) {
      setError(err as ApiError);
      setBusy(false);
      ts.current?.reset();
    }
  }

  if (configError) return <Notice title="Texhaven is unreachable" text={configError} />;
  if (!config) return <p className="mx-auto max-w-5xl px-5 py-16 text-muted" role="status">Loading...</p>;
  if (!config.sms_enabled)
    return <Notice title="Sending is not open yet" text="Join the waitlist on the home page and we will email you at launch." />;

  return (
    <div className="mx-auto grid max-w-5xl gap-10 px-5 py-10 lg:grid-cols-[1.2fr_1fr]">
      <form onSubmit={submit} className="space-y-6" noValidate>
        <div>
          <h1 className="text-3xl font-bold">Send a text</h1>
          <p className="mt-2 text-muted">The recipient sees a normal SMS. Your number stays private.</p>
        </div>

        {params.get("cancelled") && <p role="status" className="rounded-lg bg-beam/20 p-3 text-sm">Payment was cancelled. Your message was not sent.</p>}
        {config.demo_mode && (
          <p role="note" className="rounded-lg border border-beam bg-beam/10 p-3 text-sm">
            Demo mode: payments are simulated and no real SMS leaves the server.
          </p>
        )}

        <PhoneField onChange={setTo} blocked={config.blocked_countries} />

        <div>
          <label htmlFor="body" className="label">Message</label>
          <textarea id="body" rows={6} maxLength={1000} className="field" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write your message" aria-describedby="count" />
          <p id="count" className={`mt-1.5 text-sm ${overLimit ? "font-semibold text-buoy" : "text-muted"}`}>
            {info.units} characters with the safety link, {info.segments} segment{info.segments === 1 ? "" : "s"} ({info.encoding === "gsm7" ? "standard" : "unicode"} text).
            {overLimit && ` Maximum is ${config.max_segments} segments.`}
          </p>
        </div>

        <TurnstileBox ref={ts} onToken={onToken} />

        {error && (
          <div role="alert" className="rounded-lg border border-buoy/40 bg-buoy/10 p-4">
            <p className="font-semibold text-buoy">{error.message}</p>
            {error.reasons && error.reasons.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-sm">{error.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-4">
          <button className="btn-primary" disabled={!canSubmit}>
            {busy ? "Checking your message..." : `Check and pay ${price}`}
          </button>
          <p className="text-sm text-muted">Refunded automatically if delivery fails.</p>
        </div>
      </form>

      <aside aria-label="Preview" className="lg:pt-16">
        <PhoneBubble body={body} footer={footer} />
        <p className="mt-4 text-center text-sm text-muted">
          The safety link lets the recipient block you or report abuse. <Link to="/legal" className="underline underline-offset-4">Why?</Link>
        </p>
      </aside>
    </div>
  );
}

function Notice({ title, text }: { title: string; text: string }) {
  return (
    <div className="mx-auto max-w-xl px-5 py-20">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="mt-3 text-muted">{text}</p>
      <Link to="/" className="btn-primary mt-6">Back to home</Link>
    </div>
  );
}

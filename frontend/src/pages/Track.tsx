import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ApiError, api } from "../lib/api";
import { formatMoney } from "../lib/sms";
import type { MessageStatus, TrackedMessage } from "../types";

const FINAL: MessageStatus[] = ["delivered", "undelivered", "cancelled", "expired"];
const STEPS: { key: MessageStatus; label: string; at: keyof TrackedMessage }[] = [
  { key: "awaiting_payment", label: "Created", at: "created_at" },
  { key: "paid", label: "Paid", at: "paid_at" },
  { key: "sent", label: "Sent to carrier", at: "sent_at" },
  { key: "delivered", label: "Delivered", at: "delivered_at" },
];
const rank: Record<MessageStatus, number> = { awaiting_payment: 0, paid: 1, queued: 1, sent: 2, delivered: 3, undelivered: 3, cancelled: 0, expired: 0 };

const SUMMARY: Record<MessageStatus, string> = {
  awaiting_payment: "Waiting for payment.",
  paid: "Payment received. Sending now.",
  queued: "Handing your message to the carrier.",
  sent: "Sent. Waiting for the carrier to confirm delivery.",
  delivered: "Delivered.",
  undelivered: "The carrier could not deliver this message.",
  cancelled: "This message was cancelled and will not be sent.",
  expired: "Payment was not completed in time, so the message was discarded.",
};

const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleString() : "");

export default function Track() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const [msg, setMsg] = useState<TrackedMessage | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let stop = false;
    let timer: number;
    let tries = 0;
    const load = async () => {
      try {
        const m = await api.track(id);
        if (stop) return;
        setMsg(m); setError(null);
        if (FINAL.includes(m.status)) return;
      } catch (e) {
        if (stop) return;
        setError(e as ApiError);
        if ((e as ApiError).status === 404) return;
      }
      tries += 1;
      timer = window.setTimeout(load, tries < 30 ? 4000 : 15000);
    };
    load();
    return () => { stop = true; window.clearTimeout(timer); };
  }, [id]);

  if (error?.status === 404) return <Empty title="Message not found" text="Check the link. Tracking links are private and case-sensitive." />;
  if (!msg) return <p role="status" className="mx-auto max-w-2xl px-5 py-16 text-muted">{error ? error.message : "Loading..."}</p>;

  const failed = msg.status === "undelivered" || msg.status === "cancelled" || msg.status === "expired";
  const current = rank[msg.status];

  return (
    <div className="mx-auto max-w-2xl px-5 py-10">
      <h1 className="text-3xl font-bold">Message to {msg.to}</h1>
      <p role="status" aria-live="polite" className={`mt-2 text-lg font-semibold ${failed ? "text-buoy" : msg.status === "delivered" ? "text-kelp" : ""}`}>
        {SUMMARY[msg.status]}
      </p>
      {params.get("paid") && msg.status === "awaiting_payment" && (
        <p className="mt-2 text-sm text-muted">Confirming your payment with Stripe. This usually takes a few seconds.</p>
      )}
      {msg.refunded && <p className="mt-2 rounded-lg bg-kelp/15 p-3 text-sm font-semibold text-kelp">You have been refunded.</p>}

      {!failed && (
        <ol className="mt-8 space-y-4 border-l-2 border-ink/15 pl-6">
          {STEPS.map((s, i) => {
            const done = i <= current && msg[s.at];
            return (
              <li key={s.key} className="relative">
                <span className={`absolute -left-[2.15rem] top-1 h-3.5 w-3.5 rounded-full border-2 ${done ? "border-kelp bg-kelp" : "border-ink/30 bg-foam"}`} aria-hidden="true" />
                <p className={`font-semibold ${done ? "" : "text-muted"}`}>{s.label}</p>
                {done && <p className="text-sm text-muted">{fmt(msg[s.at] as string)}</p>}
              </li>
            );
          })}
        </ol>
      )}

      <dl className="mt-8 grid grid-cols-2 gap-x-6 gap-y-3 rounded-lg border border-ink/10 bg-white p-5 text-sm">
        <dt className="text-muted">Country</dt><dd className="font-semibold">{msg.country}</dd>
        <dt className="text-muted">Segments</dt><dd className="font-semibold">{msg.segments}</dd>
        <dt className="text-muted">Price</dt><dd className="font-semibold">{formatMoney(msg.price_cents, msg.currency)}</dd>
        <dt className="text-muted">Message content</dt>
        <dd className="font-semibold">{msg.content_deleted ? "Deleted" : `Deleted on ${fmt(msg.expires_at)}`}</dd>
      </dl>

      <div className="mt-6 flex flex-wrap gap-3">
        <button className="btn-ghost" onClick={() => { navigator.clipboard?.writeText(window.location.href); setCopied(true); }}>
          {copied ? "Link copied" : "Copy tracking link"}
        </button>
        <Link to="/send" className="btn-primary">Send another</Link>
      </div>
      <p className="mt-4 text-sm text-muted">Anyone with this link can see the status, so keep it private.</p>
    </div>
  );
}

function Empty({ title, text }: { title: string; text: string }) {
  return (
    <div className="mx-auto max-w-xl px-5 py-20">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="mt-3 text-muted">{text}</p>
      <Link to="/" className="btn-primary mt-6">Back to home</Link>
    </div>
  );
}

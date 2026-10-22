import { FormEvent, useCallback, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import TurnstileBox, { type TurnstileHandle } from "../components/TurnstileBox";
import { api } from "../lib/api";
import { useConfig } from "../lib/config";
import { formatMoney } from "../lib/sms";

function Hero() {
  return (
    <section className="bg-ink text-white">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 pb-20 pt-10 lg:grid-cols-[1.15fr_1fr] lg:pb-28 lg:pt-16">
        <div>
          <h1 className="text-[2.6rem] font-extrabold leading-[1.02] sm:text-6xl">
            Send a text from any browser. Scams never reach the other side.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-mist">
            Type a number, write your message, pay, done. No app and no account. Texhaven reads every
            message before it goes out and refuses the ones that look like phishing, threats or abuse.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/send" className="btn-beam">Send a text</Link>
            <Link to="/checker" className="btn border border-white/25 text-white hover:bg-white/10">Check a suspicious message</Link>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-sm" aria-label="Example of Texhaven screening two messages">
          <div className="relative space-y-4 overflow-hidden rounded-[2rem] border-[6px] border-white/20 bg-tide p-5">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-16 animate-sweep bg-gradient-to-b from-transparent via-beam/40 to-transparent" aria-hidden="true" />
            <div>
              <p className="rounded-2xl rounded-bl-sm bg-white/10 p-3 text-sm">
                Your bank account is suspended. Verify KYC now: hdfc-secure.xyz/login
              </p>
              <p className="mt-2 flex items-start gap-2 text-sm font-semibold text-[#FF8A78]">
                <span aria-hidden="true">&#x2715;</span> Not sent. Fake login link, pressure to act today.
              </p>
            </div>
            <div>
              <p className="rounded-2xl rounded-bl-sm bg-white/10 p-3 text-sm">Running ten minutes late, save me a seat?</p>
              <p className="mt-2 flex items-start gap-2 text-sm font-semibold text-[#6FE0BC]">
                <span aria-hidden="true">&#x2713;</span> Delivered. Nothing suspicious found.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const steps = [
  ["Write it", "Enter the mobile number and your message. A phone preview shows what the recipient will read."],
  ["We check it", "Rules, link analysis and an AI second opinion screen the text. Unsafe messages stop here."],
  ["Pay once", "Pay by card through Stripe. No account, and you are refunded if delivery fails."],
  ["Track it", "You get a private link that shows when the text is delivered. The content is deleted after 48 hours."],
];

const protections = [
  ["Scam and phishing screen", "Fake bank alerts, OTP requests, prize and delivery scams are refused before they cost anyone anything.", "border-buoy"],
  ["Link inspection", "Look-alike domains, hidden redirects, raw IP links and known-dangerous sites are flagged.", "border-buoy"],
  ["Paid and rate-limited", "Payment happens before sending, and each number can only be texted a couple of times a day.", "border-beam"],
  ["Recipients stay in control", "Every text carries a link to block the number or report abuse. Replying STOP works too.", "border-beam"],
  ["Encrypted, then deleted", "Numbers and messages are encrypted at rest and wiped after 48 hours.", "border-kelp"],
  ["Bot protection", "Cloudflare Turnstile and per-IP limits keep automated spam out.", "border-kelp"],
];

function QuickCheck() {
  const nav = useNavigate();
  const [text, setText] = useState("");
  return (
    <section className="bg-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-16 lg:grid-cols-2">
        <div>
          <h2 className="text-3xl font-bold">Got a text you do not trust?</h2>
          <p className="mt-3 max-w-md text-muted">
            Paste it here. You get a risk score and a plain-English explanation. It is free, and we do not store what you paste.
          </p>
        </div>
        <form
          onSubmit={(e) => { e.preventDefault(); nav("/checker", { state: { text } }); }}
          className="space-y-3"
        >
          <label htmlFor="qc" className="label">Suspicious message</label>
          <textarea id="qc" rows={4} maxLength={1000} className="field" value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Paste the text message here" />
          <button className="btn-primary" disabled={!text.trim()}>Check this message</button>
        </form>
      </div>
    </section>
  );
}

function Waitlist() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [state, setState] = useState<"idle" | "busy" | "done">("idle");
  const [error, setError] = useState("");
  const ts = useRef<TurnstileHandle>(null);
  const onToken = useCallback((t: string) => setToken(t), []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setState("busy"); setError("");
    try { await api.waitlist(email, token); setState("done"); }
    catch (err) { setError((err as Error).message); setState("idle"); ts.current?.reset(); }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-6 max-w-md space-y-3 text-left">
      {state === "done" ? (
        <p role="status" className="rounded-lg bg-kelp/15 p-4 font-semibold text-kelp">You are on the list. We will email you when sending opens.</p>
      ) : (
        <>
          <label htmlFor="wl" className="label">Email address</label>
          <div className="flex gap-2">
            <input id="wl" type="email" required className="field" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            <button className="btn-beam shrink-0" disabled={state === "busy" || !token}>Join waitlist</button>
          </div>
          <TurnstileBox ref={ts} onToken={onToken} />
          {error && <p role="alert" className="text-sm font-semibold text-[#FF8A78]">{error}</p>}
        </>
      )}
    </form>
  );
}

export default function Landing() {
  const { config } = useConfig();
  return (
    <>
      <Hero />

      <section className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="text-3xl font-bold">How sending works</h2>
        <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map(([title, text], i) => (
            <li key={title} className="border-t-2 border-ink pt-3">
              <p className="font-display text-sm font-bold text-muted">Step {i + 1}</p>
              <h3 className="mt-1 text-xl font-bold">{title}</h3>
              <p className="mt-2 text-muted">{text}</p>
            </li>
          ))}
        </ol>
        {config && (
          <p className="mt-8 text-muted">
            Pricing: {formatMoney(config.price_per_segment_cents, config.currency)} per 160-character segment, paid per message. No subscription.
          </p>
        )}
      </section>

      <section className="border-y border-ink/10 bg-white/60">
        <div className="mx-auto max-w-6xl px-5 py-16">
          <h2 className="text-3xl font-bold">What protects every message</h2>
          <dl className="mt-8 grid gap-x-10 gap-y-7 md:grid-cols-2">
            {protections.map(([term, desc, color]) => (
              <div key={term} className={`border-l-4 pl-4 ${color}`}>
                <dt className="font-display text-lg font-bold">{term}</dt>
                <dd className="mt-1 text-muted">{desc}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <QuickCheck />

      <section className="bg-ink text-white">
        <div className="mx-auto max-w-3xl px-5 py-16 text-center">
          {config && !config.sms_enabled ? (
            <>
              <h2 className="text-3xl font-bold">Sending opens soon</h2>
              <p className="mt-3 text-mist">Join the waitlist and we will email you once, on launch day.</p>
              <Waitlist />
            </>
          ) : (
            <>
              <h2 className="text-3xl font-bold">Send your first text in under a minute</h2>
              <p className="mt-3 text-mist">No sign-up. Your number is never shown to the recipient.</p>
              <Link to="/send" className="btn-beam mt-6">Send a text</Link>
            </>
          )}
        </div>
      </section>
    </>
  );
}

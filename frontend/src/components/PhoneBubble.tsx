/** A phone-style preview of the SMS as the recipient will see it. */
export default function PhoneBubble({ body, footer }: { body: string; footer: string }) {
  return (
    <div className="mx-auto w-full max-w-[19rem] rounded-[2rem] border-[6px] border-ink bg-white p-4 shadow-xl shadow-ink/10">
      <div className="mx-auto mb-4 h-1.5 w-16 rounded-full bg-ink/15" />
      <p className="mb-3 text-center text-xs text-muted">Text message</p>
      <div className="min-h-[7rem] rounded-2xl rounded-bl-sm bg-foam p-3 text-[0.95rem] leading-snug">
        <p className="whitespace-pre-wrap break-words">
          {body || <span className="text-muted">Your message appears here.</span>}
        </p>
        <p className="mt-2 whitespace-pre-wrap break-all border-t border-ink/10 pt-2 text-xs text-muted">{footer.trim()}</p>
      </div>
    </div>
  );
}

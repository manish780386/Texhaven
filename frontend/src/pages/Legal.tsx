export default function Legal() {
  return (
    <article className="mx-auto max-w-2xl px-5 py-10 leading-relaxed">
      <h1 className="text-3xl font-bold">Safety, privacy and acceptable use</h1>

      <h2 className="mt-8 text-xl font-bold">What you may not send</h2>
      <p className="mt-2 text-muted">
        Threats, harassment, scams, phishing, extortion, unsolicited marketing, or anything illegal. Texhaven screens
        messages automatically and refuses the ones that look unsafe. Repeat abuse leads to numbers being blocked and,
        where the law requires it, to information being shared with authorities.
      </p>

      <h2 className="mt-8 text-xl font-bold">Why every text has a safety link</h2>
      <p className="mt-2 text-muted">
        Each message ends with a link that lets the recipient block the number or report abuse. Recipients can also reply
        STOP. This is what keeps anonymous-style messaging from being turned against people.
      </p>

      <h2 className="mt-8 text-xl font-bold">What we store</h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
        <li>The recipient number and message text, encrypted, deleted after 48 hours.</li>
        <li>Hashed (not readable) identifiers used for rate limits and the block list.</li>
        <li>Payment is handled by Stripe. We never see or store your card details.</li>
        <li>Basic security logs without phone numbers, message text or raw IP addresses.</li>
      </ul>

      <h2 className="mt-8 text-xl font-bold">The scam checker</h2>
      <p className="mt-2 text-muted">Text you paste into the checker is analysed and discarded. It may be sent to an AI model for a second opinion when the result is borderline.</p>

      <p className="mt-8 text-sm text-muted">
        This page is a plain-language summary, not legal advice. Replace it with reviewed terms before launching to the public.
      </p>
    </article>
  );
}

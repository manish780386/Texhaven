export default function Logo({ light = false }: { light?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 font-display text-xl font-extrabold">
      <svg width="28" height="28" viewBox="0 0 64 64" aria-hidden="true">
        <path d="M32 6 10 15v16c0 14 9.4 24.6 22 28 12.6-3.4 22-14 22-28V15Z" fill={light ? "#17394D" : "#0C2231"} stroke="#F5A623" strokeWidth="4" strokeLinejoin="round" />
        <path d="M22 28h20M22 37h12" stroke="#EDF3F1" strokeWidth="4.5" strokeLinecap="round" />
      </svg>
      <span className={light ? "text-white" : "text-ink"}>Texhaven</span>
    </span>
  );
}

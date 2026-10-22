import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useConfig } from "../lib/config";

/** Demo-only checkout. Real deployments use Stripe Checkout and never show this page. */
export default function MockPay() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const { config } = useConfig();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function pay() {
    setBusy(true); setError("");
    try { await api.mockPay(id); nav(`/track/${id}?paid=1`); }
    catch (e) { setError((e as Error).message); setBusy(false); }
  }

  if (config && !config.demo_mode)
    return <p className="mx-auto max-w-xl px-5 py-20 text-muted">Demo checkout is turned off.</p>;

  return (
    <div className="mx-auto max-w-md px-5 py-20">
      <h1 className="text-3xl font-bold">Demo checkout</h1>
      <p className="mt-3 text-muted">No card is charged. This simulates a successful Stripe payment so you can try the whole flow.</p>
      {error && <p role="alert" className="mt-4 font-semibold text-buoy">{error}</p>}
      <button className="btn-primary mt-6" onClick={pay} disabled={busy}>{busy ? "Processing..." : "Simulate payment"}</button>
    </div>
  );
}

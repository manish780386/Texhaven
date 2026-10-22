import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Logo from "./Logo";

const nav = "rounded px-2 py-1 text-sm font-semibold hover:underline underline-offset-4";

export default function Layout() {
  const { pathname } = useLocation();
  useEffect(() => window.scrollTo(0, 0), [pathname]);
  const onHero = pathname === "/";

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-beam focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className={onHero ? "bg-ink text-white" : "border-b border-ink/10"}>
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link to="/" aria-label="Texhaven home"><Logo light={onHero} /></Link>
          <nav className="flex items-center gap-2 sm:gap-4" aria-label="Main">
            <NavLink to="/checker" className={nav}>Scam checker</NavLink>
            <NavLink to="/legal" className={`${nav} hidden sm:inline`}>Safety and privacy</NavLink>
            <Link to="/send" className={onHero ? "btn-beam !py-2" : "btn-primary !py-2"}>Send a text</Link>
          </nav>
        </div>
      </header>
      <main id="main" className="flex-1"><Outlet /></main>
      <footer className="border-t border-ink/10 bg-white/50">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-6 text-sm text-muted sm:flex-row sm:justify-between">
          <p>&copy; {new Date().getFullYear()} Texhaven. Messages are deleted after 48 hours.</p>
          <p className="flex gap-4">
            <Link className="underline underline-offset-4" to="/legal">Acceptable use</Link>
            <Link className="underline underline-offset-4" to="/checker">Check a message</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}

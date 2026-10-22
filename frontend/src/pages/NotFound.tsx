import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-5 py-20">
      <h1 className="text-3xl font-bold">Page not found</h1>
      <p className="mt-3 text-muted">The page you are looking for does not exist.</p>
      <Link to="/" className="btn-primary mt-6">Back to home</Link>
    </div>
  );
}

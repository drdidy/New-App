import Link from "next/link";

// A missing page, kept in the journal's voice — never Next's unstyled default.
export default function NotFound() {
  return (
    <main className="pg" style={{ textAlign: "center", paddingTop: 80 }}>
      <p className="pg-date">Page not found</p>
      <h1 className="pg-title" style={{ fontStyle: "italic" }}>This page isn&apos;t in the ledger.</h1>
      <div className="pg-rule" style={{ maxWidth: 240, margin: "0 auto 26px" }} />
      <p className="sec-sub" style={{ marginBottom: 26 }}>
        Whatever was here has been struck from the record — or never existed.
      </p>
      <Link href="/" className="btn">Return to Today</Link>
    </main>
  );
}

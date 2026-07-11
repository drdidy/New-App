"use client";

// Runtime-error boundary, in the journal's voice. Your data is untouched in
// local storage — this only replaces the crashed view.
export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="pg" style={{ textAlign: "center", paddingTop: 80 }}>
      <p className="pg-date">A smudge in the ink</p>
      <h1 className="pg-title" style={{ fontStyle: "italic" }}>Something went wrong.</h1>
      <div className="pg-rule" style={{ maxWidth: 240, margin: "0 auto 26px" }} />
      <p className="sec-sub" style={{ marginBottom: 26 }}>
        Your money data is safe on this device — this screen just stumbled. Try again.
      </p>
      <button className="btn" onClick={reset}>Reload this page</button>
    </main>
  );
}

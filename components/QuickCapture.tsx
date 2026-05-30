"use client";

import { useRef, useState } from "react";
import { useStore } from "@/lib/store";
import type { ParsedEntry } from "@/lib/types";
import Burst from "@/components/Burst";

export default function QuickCapture() {
  const { applyParsedEntries, addTransaction } = useStore();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [confirms, setConfirms] = useState<string[]>([]);
  const [celebrate, setCelebrate] = useState(0);
  const [err, setErr] = useState("");
  const recogRef = useRef<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function submit() {
    const value = text.trim();
    if (!value || busy) return;
    setBusy(true);
    setErr("");
    try {
      const res = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong.");
      const entries: ParsedEntry[] = data.entries || [];
      if (entries.length === 0) {
        setErr("I couldn't find anything to log there. Try being specific, like \"spent 20 on lunch\".");
      } else {
        applyParsedEntries(entries);
        setConfirms(entries.map((e) => e.summary));
        setText("");
        setCelebrate((n) => n + 1);
        if (navigator.vibrate) navigator.vibrate(18);
        setTimeout(() => setConfirms([]), 6000);
      }
    } catch (e: any) {
      setErr(e.message || "Network error.");
    } finally {
      setBusy(false);
    }
  }

  function toggleVoice() {
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SR) {
      setErr("Voice input isn't supported in this browser. Try typing instead.");
      return;
    }
    if (listening) {
      recogRef.current?.stop();
      return;
    }
    const recog = new SR();
    recog.lang = "en-US";
    recog.interimResults = true;
    recog.continuous = false;
    recog.onresult = (ev: any) => {
      let t = "";
      for (let i = 0; i < ev.results.length; i++) t += ev.results[i][0].transcript;
      setText(t);
    };
    recog.onerror = () => setListening(false);
    recog.onend = () => setListening(false);
    recogRef.current = recog;
    setListening(true);
    setErr("");
    recog.start();
  }

  async function onReceipt(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    setErr("");
    try {
      const dataUrl = await fileToDataUrl(file);
      const res = await fetch("/api/parse-receipt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: dataUrl }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Couldn't read that image.");
      if (!data.found) {
        setErr("I couldn't read a total on that one. Try a clearer photo, or just type it.");
      } else {
        addTransaction({
          type: "expense",
          amount: Math.abs(data.amount),
          category: data.category || "Other",
          description: data.merchant || "Receipt",
          date: new Date().toISOString().slice(0, 10),
        });
        setConfirms([data.summary || `Logged ${data.amount}`]);
        setCelebrate((n) => n + 1);
        if (navigator.vibrate) navigator.vibrate(18);
        setTimeout(() => setConfirms([]), 6000);
      }
    } catch (e: any) {
      setErr(e.message || "Network error.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card capture">
      {celebrate > 0 && <Burst key={celebrate} />}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={'Just say it — "spent 40 on gas and I still owe James 200"'}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
        }}
      />
      <div className="capture-actions">
        <button
          className={"btn btn-mic" + (listening ? " live" : "")}
          onClick={toggleVoice}
          aria-label="Voice input"
          type="button"
        >
          {listening ? "●" : "🎤"}
        </button>
        <button
          className="btn btn-ghost btn-mic"
          onClick={() => fileRef.current?.click()}
          aria-label="Snap a receipt"
          type="button"
          style={{ width: 54, flex: "0 0 54px" }}
        >
          📷
        </button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? "Thinking…" : "Log it"}
        </button>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={onReceipt}
        hidden
      />
      <p className="hint">
        Type or tap 🎤 to speak. Snap a receipt with 📷. One sentence can log
        several things at once.
      </p>
      {confirms.length > 0 && (
        <div className="confirms">
          {confirms.map((c, i) => (
            <div className="confirm" key={i}>
              ✓ {c}
            </div>
          ))}
        </div>
      )}
      {err && <p className="err">{err}</p>}
    </div>
  );
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

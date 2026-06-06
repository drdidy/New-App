"use client";

import { useRef, useState } from "react";
import { Camera, CheckCircle2, Loader2, Mic, Send } from "lucide-react";
import { useStore } from "@/lib/store";
import type { ParsedEntry } from "@/lib/types";
import { todayISO } from "@/lib/format";
import MemberPicker from "@/components/MemberPicker";

export default function QuickCapture() {
  const { data, applyParsedEntries, addTransaction } = useStore();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [confirms, setConfirms] = useState<string[]>([]);
  const [err, setErr] = useState("");
  const [who, setWho] = useState<string | undefined>(data.members[0]?.id);
  const recogRef = useRef<any>(null);
  const finalRef = useRef("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function submit(override?: string) {
    const value = (typeof override === "string" ? override : text).trim();
    if (!value || busy) return;
    setBusy(true);
    setErr("");
    try {
      const res = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      const parsed = await res.json();
      if (!res.ok) throw new Error(parsed.error || "Something went wrong.");
      const entries: ParsedEntry[] = parsed.entries || [];
      if (entries.length === 0) {
        setErr('Try a money sentence like "spent 20 on lunch" or "paid Visa 75".');
      } else {
        applyParsedEntries(entries, who);
        setConfirms(entries.map((e) => e.summary));
        setText("");
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
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErr("Voice input is not supported in this browser. Typing still works.");
      return;
    }
    if (listening) {
      recogRef.current?.stop();
      return;
    }
    const recog = new SpeechRecognition();
    recog.lang = "en-US";
    recog.interimResults = true;
    recog.continuous = false;
    finalRef.current = "";
    recog.onresult = (ev: any) => {
      let transcript = "";
      for (let i = 0; i < ev.results.length; i++) {
        transcript += ev.results[i][0].transcript;
      }
      finalRef.current = transcript;
      setText(transcript);
    };
    recog.onerror = (ev: any) => {
      setListening(false);
      if (ev?.error === "not-allowed" || ev?.error === "service-not-allowed") {
        setErr("Microphone access was blocked. Allow the mic for this site to use voice capture.");
      } else if (ev?.error === "no-speech") {
        setErr("I did not catch anything. Try again or type the transaction.");
      } else if (ev?.error !== "aborted") {
        setErr("Voice input had a problem. Typing still works.");
      }
    };
    recog.onend = () => {
      setListening(false);
      const value = finalRef.current.trim();
      finalRef.current = "";
      if (value) submit(value);
    };
    recogRef.current = recog;
    setListening(true);
    setErr("");
    try {
      recog.start();
    } catch {
      setListening(false);
      setErr("Could not start the microphone. Typing still works.");
    }
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
      const parsed = await res.json();
      if (!res.ok) throw new Error(parsed.error || "Could not read that image.");
      if (!parsed.found) {
        setErr("I could not read a total. Try a clearer receipt photo, or type the total.");
      } else {
        const items = Array.isArray(parsed.items)
          ? parsed.items
              .filter((x: any) => x && typeof x.name === "string" && Number(x.amount) > 0)
              .slice(0, 80)
              .map((x: any) => ({
                name: String(x.name).slice(0, 80),
                amount: Math.abs(Number(x.amount)),
                category: String(x.category || "Other").slice(0, 40),
                quantity: x.quantity ? Number(x.quantity) : undefined,
              }))
          : undefined;
        addTransaction({
          type: "expense",
          amount: Math.abs(parsed.amount),
          category: parsed.category || "Other",
          description: parsed.merchant || "Receipt",
          date: todayISO(),
          memberId: who,
          lineItems: items && items.length > 0 ? items : undefined,
        });
        setConfirms([
          parsed.summary || `Logged ${parsed.amount}`,
          ...(items?.length ? [`Captured ${items.length} receipt line items`] : []),
        ]);
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
      <label className="capture-label" htmlFor="quick-capture">
        Tell Money Coach what happened
      </label>
      <textarea
        id="quick-capture"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={'Examples: "spent 42 on groceries", "paid Visa 75", "paycheck 2200"'}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
        }}
      />
      {data.members.length > 1 && (
        <div className="capture-who">
          <span className="capture-who-label">Assign to</span>
          <MemberPicker
            members={data.members}
            value={who}
            onChange={setWho}
            size="sm"
          />
        </div>
      )}
      <div className="capture-actions">
        <button
          className={"btn btn-mic" + (listening ? " live" : "")}
          onClick={toggleVoice}
          aria-label={listening ? "Stop voice capture" : "Start voice capture"}
          type="button"
        >
          <Mic size={19} aria-hidden="true" />
        </button>
        <button
          className="btn btn-ghost btn-mic"
          onClick={() => fileRef.current?.click()}
          aria-label="Scan receipt"
          type="button"
        >
          <Camera size={19} aria-hidden="true" />
        </button>
        <button className="btn btn-primary" onClick={() => submit()} disabled={busy}>
          {busy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
          {busy ? "Analyzing" : "Log entry"}
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
        AI capture sends this note or receipt image for analysis. You can always type manually.
      </p>
      {confirms.length > 0 && (
        <div className="confirms">
          {confirms.map((c) => (
            <div className="confirm" key={c}>
              <CheckCircle2 size={16} aria-hidden="true" />
              {c}
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

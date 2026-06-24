"use client";

import { useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { Loader2, Mic, Send, Sparkles, X } from "lucide-react";
import { useStore } from "@/lib/store";
import type { ParsedEntry } from "@/lib/types";
import { postJson } from "@/lib/clientApi";

const EXAMPLES = [
  "spent 40 on gas",
  "my checking has 1850",
  "rent is 1400 due on the 1st",
  "I owe 3000 on my Visa at 22%",
  "budget 300 for dining",
  "emergency fund goal of 6000",
];

// A global, speak-anywhere capture. Tap the mic (or type), and one natural
// sentence becomes the right thing: an expense, a debt, an account balance, a
// bill, a budget, or a savings goal — no forms.
export default function SpeakButton() {
  const { applyParsedEntries, data } = useStore();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [confirms, setConfirms] = useState<string[]>([]);
  const [err, setErr] = useState("");
  const recogRef = useRef<any>(null);
  const finalRef = useRef("");

  function close() {
    recogRef.current?.stop?.();
    setOpen(false);
    setText("");
    setErr("");
    setConfirms([]);
    setListening(false);
  }

  async function submit(override?: string) {
    const value = (typeof override === "string" ? override : text).trim();
    if (!value || busy) return;
    setBusy(true);
    setErr("");
    setConfirms([]);
    const r = await postJson<{ entries: ParsedEntry[] }>("/api/parse", { text: value });
    setBusy(false);
    if (!r.ok) {
      setErr(r.error || "Something went wrong.");
      return;
    }
    const entries: ParsedEntry[] = r.data?.entries || [];
    if (entries.length === 0) {
      setErr('I didn’t catch anything to add. Try "spent 20 on lunch" or "rent is 1400 on the 1st".');
      return;
    }
    applyParsedEntries(entries, data.members[0]?.id);
    setConfirms(entries.map((e) => e.summary));
    setText("");
    if (navigator.vibrate) navigator.vibrate(18);
  }

  function toggleVoice() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setErr("Voice isn’t supported in this browser — type below, or use your keyboard’s mic. 🙂");
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
    finalRef.current = "";
    recog.onresult = (ev: any) => {
      let t = "";
      for (let i = 0; i < ev.results.length; i++) t += ev.results[i][0].transcript;
      finalRef.current = t;
      setText(t);
    };
    recog.onerror = (ev: any) => {
      setListening(false);
      if (ev?.error === "not-allowed" || ev?.error === "service-not-allowed") {
        setErr("Microphone access is blocked. Allow the mic for this site, then try again.");
      } else if (ev?.error === "no-speech") {
        setErr("I didn’t catch that — tap the mic and try again.");
      } else if (ev?.error !== "aborted") {
        setErr("Voice had a problem. Typing still works.");
      }
    };
    recog.onend = () => {
      setListening(false);
      const v = finalRef.current.trim();
      finalRef.current = "";
      if (v) submit(v);
    };
    recogRef.current = recog;
    setListening(true);
    setErr("");
    try {
      recog.start();
    } catch {
      setListening(false);
      setErr("Couldn’t start the microphone. Typing still works.");
    }
  }

  // The Coach tab has its own mic + input, so the global FAB would collide with
  // it — hide it there.
  if (pathname === "/coach" || pathname.startsWith("/advisor")) return null;

  return (
    <>
      <button className="mc-fab" onClick={() => setOpen(true)} aria-label="Add by voice">
        <Mic size={22} />
      </button>

      {open && (
        <div className="lx-sheet-backdrop" onClick={close}>
          <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="lx-sheet-head">
              <h3>Just say it</h3>
              <button className="lx-sheet-x" onClick={close} aria-label="Close"><X size={18} /></button>
            </div>

            <button
              className={"mc-bigmic" + (listening ? " live" : "")}
              onClick={toggleVoice}
              aria-label={listening ? "Stop listening" : "Start talking"}
            >
              {busy ? <Loader2 size={30} className="spin" /> : <Mic size={30} />}
              <span>{listening ? "Listening… tap to stop" : busy ? "Adding…" : "Tap & talk"}</span>
            </button>

            <div className="mc-or">or type / use your keyboard mic</div>

            <div className="lx-chatbar" style={{ paddingTop: 0 }}>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
                placeholder='e.g. "rent is 1400 on the 1st"'
                autoFocus
              />
              <button aria-label="Add" onClick={() => submit()} disabled={busy || !text.trim()}><Send size={18} /></button>
            </div>

            {err && <p className="lx-voicenote">{err}</p>}

            {confirms.length > 0 ? (
              <div className="mc-confirms">
                {confirms.map((c, i) => (
                  <div className="mc-confirm" key={i}><Sparkles size={13} /> {c}</div>
                ))}
                <button className="lx-ghost" style={{ width: "100%", marginTop: 4 }} onClick={() => setConfirms([])}>Add another</button>
              </div>
            ) : (
              <div className="mc-hints">
                <span className="mc-hints-label">Try saying</span>
                {EXAMPLES.map((ex) => (
                  <button key={ex} className="lx-chip" onClick={() => submit(ex)}>{ex}</button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

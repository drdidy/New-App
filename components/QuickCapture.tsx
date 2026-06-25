"use client";

import { useRef, useState } from "react";
import { Camera, CheckCircle2, Loader2, Mic, Send } from "lucide-react";
import { useStore } from "@/lib/store";
import { matchPersonDebts } from "@/lib/insights";
import type { Debt, ParsedEntry } from "@/lib/types";
import { todayISO, formatMoney } from "@/lib/format";
import { postJson, compressImage } from "@/lib/clientApi";
import MemberPicker from "@/components/MemberPicker";

interface PendingPay {
  amount: number;
  party: string;
  summary: string;
  candidates: Debt[];
}

interface ReceiptResp {
  found: boolean;
  amount: number;
  merchant?: string;
  category?: string;
  items?: Array<{ name: string; amount: number; category?: string; quantity?: number }>;
  summary?: string;
}

export default function QuickCapture() {
  const { data, applyParsedEntries, addTransaction, payDebt } = useStore();
  const cur = data.currency;
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [confirms, setConfirms] = useState<string[]>([]);
  const [pending, setPending] = useState<PendingPay[]>([]);
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
    const r = await postJson<{ entries: ParsedEntry[] }>("/api/parse", { text: value });
    setBusy(false);
    if (!r.ok) {
      setErr(r.error || "Something went wrong.");
      return;
    }
    const entries: ParsedEntry[] = r.data?.entries || [];
    if (entries.length === 0) {
      setErr('Try a money sentence like "spent 20 on lunch" or "paid Visa 75".');
      return;
    }
    // A payment to a person whose name matches more than one debt is ambiguous
    // ("James" → James Allen or James Brown). Hold those for a quick confirm;
    // apply everything else (incl. unambiguous / exact matches) immediately.
    const immediate: ParsedEntry[] = [];
    const ambiguous: PendingPay[] = [];
    for (const e of entries) {
      if (e.kind === "debt_payment") {
        const { exact, candidates } = matchPersonDebts(data.debts, e.party || "");
        if (!exact && candidates.length >= 2) {
          ambiguous.push({ amount: Math.abs(e.amount), party: e.party || "", summary: e.summary, candidates });
          continue;
        }
      }
      immediate.push(e);
    }
    if (immediate.length) applyParsedEntries(immediate, who);
    setConfirms(immediate.map((e) => e.summary));
    setPending(ambiguous);
    setText("");
    if (navigator.vibrate) navigator.vibrate(18);
    if (immediate.length) setTimeout(() => setConfirms([]), 6000);
  }

  function resolveToDebt(idx: number, debt: Debt) {
    const p = pending[idx];
    if (!p) return;
    payDebt(debt.id, p.amount, who);
    setPending((list) => list.filter((_, i) => i !== idx));
    setConfirms((c) => [...c, `Paid ${formatMoney(p.amount, cur)} to ${debt.party} — ${formatMoney(Math.max(0, debt.balance - p.amount), cur)} left`]);
    if (navigator.vibrate) navigator.vibrate(18);
  }

  function resolveToExpense(idx: number) {
    const p = pending[idx];
    if (!p) return;
    addTransaction({ type: "expense", amount: p.amount, category: "Debt payment", description: p.summary || `Payment to ${p.party}`, date: todayISO(), memberId: who });
    setPending((list) => list.filter((_, i) => i !== idx));
    setConfirms((c) => [...c, `Logged ${formatMoney(p.amount, cur)} as an expense`]);
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
    const dataUrl = await compressImage(file);
    if (!dataUrl) {
      setBusy(false);
      setErr("Couldn’t read that image. Try another photo or type the total.");
      return;
    }
    const r = await postJson<ReceiptResp>("/api/parse-receipt", { image: dataUrl });
    setBusy(false);
    if (!r.ok) {
      setErr(r.error || "Could not read that image.");
      return;
    }
    const parsed = r.data;
    if (!parsed || !parsed.found || !(Number(parsed.amount) > 0)) {
      setErr("I couldn’t read a total. Try a clearer receipt photo, or type the total.");
      return;
    }
    const items = Array.isArray(parsed.items)
      ? parsed.items
          .filter((x) => x && typeof x.name === "string" && Number.isFinite(Number(x.amount)) && Number(x.amount) > 0)
          .slice(0, 80)
          .map((x) => ({
            name: String(x.name).slice(0, 80),
            amount: Math.abs(Number(x.amount)),
            category: String(x.category || "Other").slice(0, 40),
            quantity: x.quantity && Number.isFinite(Number(x.quantity)) ? Number(x.quantity) : undefined,
          }))
      : undefined;
    addTransaction({
      type: "expense",
      amount: Math.abs(Number(parsed.amount)),
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

  return (
    <div className="card capture">
      <label className="capture-label" htmlFor="quick-capture">
        Tell Money Coach what happened
      </label>
      <textarea
        id="quick-capture"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Try: spent 42 on groceries, paid Visa 75, paycheck 2200"
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
        Only the note or receipt you choose is analyzed. You can always type manually.
      </p>
      {pending.map((p, idx) => (
        <div className="capture-resolve" key={idx}>
          <div className="capture-resolve-q">
            You paid <b>{formatMoney(p.amount, cur)}</b> to “{p.party}” — which debt should I reduce?
          </div>
          <div className="capture-resolve-opts">
            {p.candidates.map((c) => (
              <button key={c.id} className="lx-ghost sm" onClick={() => resolveToDebt(idx, c)}>
                {c.party} · {formatMoney(c.balance, cur)} left
              </button>
            ))}
            <button className="lx-ghost sm" onClick={() => resolveToExpense(idx)}>Just an expense</button>
          </div>
        </div>
      ))}
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

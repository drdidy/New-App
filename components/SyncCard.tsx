"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";

const WORDS = [
  "otter", "maple", "river", "cocoa", "ember", "pebble", "willow", "mango",
  "harbor", "cedar", "olive", "sunny", "ginger", "violet", "comet",
  "orchard", "silver", "meadow", "copper", "jasper",
];

function suggestCode() {
  const a = WORDS[Math.floor(Math.random() * WORDS.length)];
  const b = WORDS[Math.floor(Math.random() * WORDS.length)];
  const c = WORDS[Math.floor(Math.random() * WORDS.length)];
  const n = Math.random().toString(36).slice(2, 8);
  return `${a}-${b}-${c}-${n}`;
}

export default function SyncCard() {
  const { data, setSync, syncNow, syncState } = useStore();
  const [editing, setEditing] = useState(false);
  const [code, setCode] = useState(data.syncCode || suggestCode());
  const [copied, setCopied] = useState(false);

  const on = Boolean(data.syncEnabled && data.syncCode);

  function connect() {
    const c = code.trim();
    if (c.length < 16) return;
    setSync(true, c);
    setEditing(false);
  }

  function copy() {
    navigator.clipboard?.writeText(data.syncCode || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  const statusText =
    syncState === "syncing"
      ? "Syncing…"
      : syncState === "ok"
      ? "Synced ✓"
      : syncState === "error"
      ? "Couldn't reach sync — will retry"
      : syncState === "unconfigured"
      ? "Cloud storage isn't set up yet"
      : "Ready";

  return (
    <div className="card reveal d2">
      <div className="card-h">Sync across devices</div>

      {!on ? (
        <>
          <p className="h-sub" style={{ marginBottom: 14 }}>
            Share one household between two phones. Pick a secret code, then enter
            the <strong>same code</strong> on your partner's phone — your numbers
            stay in step automatically.
          </p>
          {!editing ? (
            <button className="btn btn-primary btn-block" onClick={() => setEditing(true)}>
              Turn on sync
            </button>
          ) : (
            <>
              <div className="field">
                <label>Household code (share this with your partner)</label>
                <div className="row">
                  <input
                    className="mini-input"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="e.g. otter-maple-river-k4p9x2"
                  />
                  <button
                    className="btn btn-ghost"
                    style={{ flex: "0 0 auto" }}
                    onClick={() => setCode(suggestCode())}
                    type="button"
                  >
                    🎲
                  </button>
                </div>
              </div>
              <div className="capture-actions">
                <button className="btn btn-ghost" onClick={() => setEditing(false)}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={connect}>
                  Connect
                </button>
              </div>
              <p className="hint" style={{ marginTop: 10 }}>
                On the second phone, install the app, open Settings → Sync, and
                enter this exact code to join. Treat it like a password for your budget.
              </p>
            </>
          )}
        </>
      ) : (
        <>
          <div className="sync-status">
            <span className={"sync-dot " + syncState} />
            <span>{statusText}</span>
          </div>
          <div className="field" style={{ marginTop: 12 }}>
            <label>Your household code</label>
            <div className="row">
              <input className="mini-input" value={data.syncCode} readOnly />
              <button className="btn btn-ghost" style={{ flex: "0 0 auto" }} onClick={copy}>
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
          <div className="capture-actions">
            <button className="btn btn-ghost" onClick={() => void syncNow()}>
              ⟳ Sync now
            </button>
            <button
              className="btn btn-ghost danger"
              onClick={() => setSync(false)}
            >
              Turn off
            </button>
          </div>
          {syncState === "unconfigured" && (
            <p className="hint" style={{ marginTop: 10 }}>
              Sync needs a small cloud add-on on your Vercel project (a free KV /
              Upstash store). Once it's added, this connects automatically.
            </p>
          )}
        </>
      )}
    </div>
  );
}

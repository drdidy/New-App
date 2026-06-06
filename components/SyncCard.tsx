"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";

const WORDS = [
  "maple", "river", "cocoa", "ember", "pebble", "willow", "mango",
  "harbor", "cedar", "olive", "sunny", "ginger", "violet", "comet",
  "orchard", "silver", "meadow", "copper", "jasper", "summit",
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
      ? "Syncing..."
      : syncState === "ok"
      ? "Synced"
      : syncState === "error"
      ? "Couldn't reach sync - will retry"
      : syncState === "unconfigured"
      ? "Cloud storage isn't set up yet"
      : "Ready";

  return (
    <div className="card reveal d2">
      <div className="card-h">Private sync</div>

      {!on ? (
        <>
          <p className="h-sub" style={{ marginBottom: 14 }}>
            Keep this profile private, or share one household across trusted devices.
            Anyone with the <strong>same code</strong> can sync this household's budget,
            so only share it with people who should see the same money plan.
          </p>
          {!editing ? (
            <button className="btn btn-primary btn-block" onClick={() => setEditing(true)}>
              Turn on household sync
            </button>
          ) : (
            <>
              <div className="field">
                <label>Private household code</label>
                <div className="row">
                  <input
                    className="mini-input"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="e.g. maple-river-summit-k4p9x2"
                  />
                  <button
                    className="btn btn-ghost"
                    style={{ flex: "0 0 auto" }}
                    onClick={() => setCode(suggestCode())}
                    type="button"
                  >
                    New
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
                On another trusted device, install the app, open Settings, and
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
              Sync now
            </button>
            <button className="btn btn-ghost danger" onClick={() => setSync(false)}>
              Turn off
            </button>
          </div>
          <p className="hint" style={{ marginTop: 10 }}>
            Sync links this household only. Separate users should create their own
            profile unless they intentionally share money with you.
          </p>
          {syncState === "unconfigured" && (
            <p className="hint" style={{ marginTop: 10 }}>
              Sync needs a small cloud add-on on your Vercel project, such as a free KV
              or Upstash store. Once it is added, this connects automatically.
            </p>
          )}
        </>
      )}
    </div>
  );
}

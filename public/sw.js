// Minimal offline-capable service worker for Money Coach.
// Strategy: network-first for navigation/app shell, falling back to cache so
// the app still opens when the phone is offline. API calls always go to network.
const CACHE = "money-coach-v50-vault";
const SHELL = [
  "/",
  "/plan",
  "/spending",
  "/debt",
  "/bills",
  "/settings",
  "/coach",
  "/buckets",
  "/ledger",
  "/week",
  "/month",
  "/manifest.webmanifest",
  "/icon.svg",
  "/icon-192.png",
  "/icon-512.png",
  "/icon-maskable-512.png",
  "/offline.html",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
      ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return; // never cache POSTs (API writes)
  const url = new URL(request.url);
  if (url.pathname.startsWith("/api/")) return; // let API hit the network

  event.respondWith(
    fetch(request)
      .then((res) => {
        // Only cache good responses — a cached 404/500 would be served offline forever.
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(request, copy).catch(() => {}));
        }
        return res;
      })
      .catch(async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        // The offline page is only a valid stand-in for page NAVIGATIONS.
        // Serving HTML as the body of a failed script/CSS request corrupts the app.
        if (request.mode === "navigate") {
          const offline = await caches.match("/offline.html");
          if (offline) return offline;
          const home = await caches.match("/");
          if (home) return home;
        }
        return Response.error();
      }),
  );
});

// --- Weekly Edition reminder -------------------------------------------------
// Fired by the Periodic Background Sync API (registered from the app when the
// user turns reminders on). Announces each new ISO week's issue exactly once,
// using a cache entry as the "already announced" marker since the SW has no
// localStorage.
function swIsoWeekId(d) {
  const t = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  t.setDate(t.getDate() + 3 - ((t.getDay() + 6) % 7));
  const jan4 = new Date(t.getFullYear(), 0, 4);
  const wk = 1 + Math.round(((t.getTime() - jan4.getTime()) / 86400000 - 3 + ((jan4.getDay() + 6) % 7)) / 7);
  return `${t.getFullYear()}-W${String(wk).padStart(2, "0")}`;
}

self.addEventListener("periodicsync", (event) => {
  if (event.tag !== "weekly-edition") return;
  event.waitUntil(
    (async () => {
      if (self.Notification && self.Notification.permission !== "granted") return;
      const id = swIsoWeekId(new Date());
      const cache = await caches.open(CACHE);
      const prev = await cache.match("/__meta/week-notified");
      if (prev && (await prev.text()) === id) return;
      await cache.put("/__meta/week-notified", new Response(id));
      await self.registration.showNotification("The Weekly Edition is out", {
        body: "Your week in money, typeset. Open the new issue.",
        icon: "/icon-192.png",
        badge: "/icon-192.png",
        tag: "weekly-edition",
        data: { url: "/week" },
      });
    })(),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if ("focus" in w) {
          w.navigate(url);
          return w.focus();
        }
      }
      return self.clients.openWindow(url);
    }),
  );
});

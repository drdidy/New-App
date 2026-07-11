// Minimal offline-capable service worker for Money Coach.
// Strategy: network-first for navigation/app shell, falling back to cache so
// the app still opens when the phone is offline. API calls always go to network.
const CACHE = "money-coach-v46-edition";
const SHELL = [
  "/",
  "/plan",
  "/spending",
  "/debt",
  "/bills",
  "/settings",
  "/coach",
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

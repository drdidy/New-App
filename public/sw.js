// Minimal offline-capable service worker for Money Coach.
// Strategy: network-first for navigation/app shell, falling back to cache so
// the app still opens when the phone is offline. API calls always go to network.
const CACHE = "money-coach-v31-reorg";
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
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(request, copy).catch(() => {}));
        return res;
      })
      .catch(() =>
        caches.match(request).then((r) => r || caches.match("/offline.html") || caches.match("/")),
      ),
  );
});

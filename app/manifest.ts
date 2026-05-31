import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Money Coach",
    // short_name is what Android/iOS show under the home-screen icon — keep it
    // short so launchers don't truncate it.
    short_name: "MoneyCoach",
    description:
      "Your private, AI-powered budgeting, bills and debt coach. Just talk to it.",
    start_url: "/",
    id: "/",
    display: "standalone",
    background_color: "#fbf6f1",
    theme_color: "#d2723f",
    orientation: "portrait",
    categories: ["finance", "productivity"],
    icons: [
      // PNGs first — Android/Chrome generate the home-screen icon most reliably
      // from these. 'maskable' fills Android's adaptive-icon shape; 'any' keeps
      // the rounded tile elsewhere.
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
      // Scalable fallback.
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
    ],
  };
}

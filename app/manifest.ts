import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Money Coach",
    // Keep the launcher label aligned with the actual product name.
    short_name: "Money Coach",
    description:
      "Your private, AI-powered budgeting, bills, spending and debt coach.",
    start_url: "/",
    id: "/",
    display: "standalone",
    // Match the aurora canvas so the standalone splash/status chrome doesn't
    // flash light over a dark app at every launch.
    background_color: "#080706",
    theme_color: "#080706",
    orientation: "portrait",
    categories: ["finance", "productivity"],
    shortcuts: [
      {
        name: "Log spending",
        short_name: "Log",
        description: "Quickly capture an expense, income, or debt note.",
        url: "/",
        icons: [{ src: "/icon-192.png", sizes: "192x192", type: "image/png" }],
      },
      {
        name: "Money Coach",
        short_name: "Coach",
        description: "Ask for a budget, debt, or weekly check-in plan.",
        url: "/coach",
        icons: [{ src: "/icon-192.png", sizes: "192x192", type: "image/png" }],
      },
      {
        name: "Debt plan",
        short_name: "Debts",
        description: "Review payoff strategy and payment ideas.",
        url: "/debt",
        icons: [{ src: "/icon-192.png", sizes: "192x192", type: "image/png" }],
      },
    ],
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

import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Money Coach",
    short_name: "Coach",
    description:
      "Your private, AI-powered budgeting and debt coach. Just talk to it.",
    start_url: "/",
    display: "standalone",
    background_color: "#0e1b17",
    theme_color: "#0e1b17",
    orientation: "portrait",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
      {
        src: "/icon-maskable.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
  };
}

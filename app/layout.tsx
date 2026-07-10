import type { Metadata, Viewport } from "next";
import { Inter, Sora } from "next/font/google";
import "./globals.css";
import { StoreProvider } from "@/lib/store";
import AppShell from "@/components/AppShell";
import SwRegister from "@/components/SwRegister";

// World-class type pairing: Sora for display (headlines, money), Inter for UI.
const sora = Sora({ subsets: ["latin"], weight: ["600", "700", "800"], variable: "--font-display", display: "swap" });
const inter = Inter({ subsets: ["latin"], variable: "--font-body", display: "swap" });

export const metadata: Metadata = {
  title: "Money Coach",
  description: "Your private, AI-powered budgeting and debt coach.",
  applicationName: "Money Coach",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Money Coach",
  },
  icons: {
    icon: [
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/apple-icon.png", sizes: "180x180" }],
  },
};

export const viewport: Viewport = {
  themeColor: "#070b16",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

// Set the theme attribute before paint to avoid a flash of the wrong theme.
// Light is the default.
const themeInit = `(function(){try{var d=JSON.parse(localStorage.getItem('money-coach-data-v1')||'{}');document.documentElement.dataset.theme=d.theme==='dark'?'dark':'light';}catch(e){document.documentElement.dataset.theme='light';}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className={`${sora.variable} ${inter.variable}`}>
        <StoreProvider>
          <AppShell>{children}</AppShell>
          <SwRegister />
        </StoreProvider>
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import "./globals.css";
import { StoreProvider } from "@/lib/store";
import AppShell from "@/components/AppShell";
import SwRegister from "@/components/SwRegister";

export const metadata: Metadata = {
  title: "Money Coach",
  description: "Your private, AI-powered budgeting and debt coach.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Coach",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a1411",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

// Set the theme attribute before paint to avoid a flash of the wrong theme.
const themeInit = `(function(){try{var d=JSON.parse(localStorage.getItem('money-coach-data-v1')||'{}');document.documentElement.dataset.theme=d.theme==='light'?'light':'dark';}catch(e){document.documentElement.dataset.theme='dark';}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body>
        <StoreProvider>
          <AppShell>{children}</AppShell>
          <SwRegister />
        </StoreProvider>
      </body>
    </html>
  );
}

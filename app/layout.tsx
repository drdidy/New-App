import type { Metadata, Viewport } from "next";
import "./globals.css";
import { StoreProvider } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
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
  themeColor: "#0e1b17",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <StoreProvider>
          <div className="app">{children}</div>
          <BottomNav />
          <SwRegister />
        </StoreProvider>
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { Navbar } from "@/components/layout/Navbar";
import { Disclaimer } from "@/components/layout/Disclaimer";
import { ChatWidget } from "@/components/chat/ChatWidget";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export const metadata: Metadata = {
  title: "BharatMarkets — Indian Stock Market Tracker",
  description:
    "An educational Indian stock market tracker for NSE & BSE stocks, benchmark indices, technical indicators, and sector analysis. Educational purposes only.",
  keywords: [
    "NSE",
    "BSE",
    "Indian Stock Market",
    "NIFTY 50",
    "SENSEX",
    "Stock Tracker",
    "Technical Analysis",
    "BharatMarkets",
  ],
  authors: [{ name: "BharatMarkets" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable}`} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased text-foreground flex flex-col selection:bg-emerald-500/30 selection:text-emerald-300">
        <ThemeProvider>
          {/* Top navigation */}
          <Navbar />

          {/* Main content area */}
          <main className="flex-1 pb-16">{children}</main>

          {/* Floating AI chat on every page */}
          <ChatWidget />

          {/* Persistent legal disclaimer banner */}
          <Disclaimer />
        </ThemeProvider>
      </body>
    </html>
  );
}

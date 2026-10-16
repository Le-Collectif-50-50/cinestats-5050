import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/atoms/Navbar";
import { Toaster } from "@/components/ui/sonner";
import Footer from "@/components/atoms/Footer";
import { SearchProvider } from "@/contexts/SearchContext";
import Script from "next/script";
import {
  SITE_NAME,
  SITE_DESCRIPTION,
  DEFAULT_KEYWORDS,
} from "@/lib/seo";

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
});

export const metadata: Metadata = {
  title: {
    default: `${SITE_NAME} — Inégalités de parité dans le cinéma`,
    template: `%s | ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  authors: [{ name: "Data4Good" }, { name: "Collectif 50/50" }],
  keywords: DEFAULT_KEYWORDS,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html className="min-h-screen h-full" lang="fr">
      <head>
        {/*
          Boolean(...) matters here, not a plain `&&`: Dockerfile.prod always
          writes NEXT_PUBLIC_UMAMI_WEBSITE_ID= (empty string) to .env.local
          even when no value is passed as a build-arg — it's never actually
          `undefined` in a built image. `"" && <Script/>` evaluates to `""`,
          and React renders that as a real (if invisible) empty text node.
          Injected as a child of <head>, that empty text node collided with
          Next.js's own head-content injection and corrupted the *entire*
          server-rendered <head> (its content and the page's inlined CSS got
          concatenated into one giant text blob server-side, while the
          client rendered plain whitespace) — a server/client text mismatch
          that crashed hydration on every single page, in every environment,
          any time this env var was unset (i.e. always, apart from prod).
        */}
        {Boolean(process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID) && (
          <Script
            defer
            src="https://cloud.umami.is/script.js"
            data-website-id={process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID}
          />
        )}
      </head>
      <body
        className={`${geistSans.variable} ${geist.variable} antialiased bg-red min-h-screen h-full`}
        style={{
          background: "#0B0C0F",
        }}
        suppressHydrationWarning
      >
        <SearchProvider>
          <Navbar>{children}</Navbar>
          <Footer />
          <Toaster />
        </SearchProvider>
      </body>
    </html>
  );
}

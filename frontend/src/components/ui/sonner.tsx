"use client"

import { Toaster as Sonner, ToasterProps } from "sonner"

// No <ThemeProvider> exists anywhere in this app (it's dark-only by design —
// see the hardcoded #0B0C0F background in layout.tsx), so `useTheme()` from
// next-themes had nothing to read and fell through to sonner's theme="system"
// default. Internally, sonner resolves "system" via
// `typeof window !== 'undefined' ? window.matchMedia(...).matches ...: 'light'`
// inside a useState initializer — `window` doesn't exist during SSR (→
// 'light'), but does during the client's first render pass, before
// hydration reconciles with the server HTML. Any visitor with a dark-mode
// OS preference got 'dark' there, mismatching the server's 'light' and
// crashing hydration site-wide (Toaster renders in the root layout, on
// every page). Since there's no real light/dark switching to support here,
// just hardcode 'dark' — consistent on both server and client, no mismatch.
const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster }

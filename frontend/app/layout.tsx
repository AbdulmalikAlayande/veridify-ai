import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Veridify AI",
  description: "A unified frontend for onboarding, funding, verification, and audit history",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  )
}

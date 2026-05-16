"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
        <div className="app-frame max-w-xl space-y-5 p-8 text-center">
          <p className="section-kicker">Application error</p>
          <h1 className="font-heading text-4xl">The workspace hit an unexpected edge case.</h1>
          <p className="text-muted-foreground">
            Refresh the route or reset the boundary to continue working while we tighten the app shell.
          </p>
          <Button onClick={reset}>Try again</Button>
        </div>
      </body>
    </html>
  )
}

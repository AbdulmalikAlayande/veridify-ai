"use client"

import { useState } from "react"
import { CheckIcon, CopyIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export function CopyField({
  label,
  value,
  mono = false,
  className,
}: {
  label: string
  value: string
  mono?: boolean
  className?: string
}) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      // clipboard might be blocked; ignore silently
    }
  }

  return (
    <div
      className={cn(
        "group relative rounded-2xl border border-border/70 bg-gradient-to-br from-white/85 to-muted/40 p-4 transition-colors hover:border-primary/40",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="section-kicker">{label}</p>
        <button
          type="button"
          onClick={handleCopy}
          className={cn(
            "inline-flex size-7 items-center justify-center rounded-full border border-border/60 bg-white/70 text-muted-foreground transition-all hover:border-primary/40 hover:text-primary",
            copied && "border-emerald-300 bg-emerald-50 text-emerald-600",
          )}
          aria-label={`Copy ${label}`}
        >
          {copied ? <CheckIcon className="size-3.5" /> : <CopyIcon className="size-3.5" />}
        </button>
      </div>
      <p className={cn("mt-2 break-all text-foreground", mono ? "font-mono text-sm" : "text-base font-semibold")}>
        {value}
      </p>
    </div>
  )
}

import type { Verdict } from "@/lib/types"
import { cn } from "@/lib/utils"

const badgeStyles: Record<Verdict, string> = {
  AUTHENTIC: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  MANIPULATED: "bg-amber-100 text-amber-800 ring-amber-200",
  SYNTHETIC: "bg-rose-100 text-rose-800 ring-rose-200",
}

export function StatusBadge({
  verdict,
  className,
}: {
  verdict: Verdict
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ring-1",
        badgeStyles[verdict],
        className,
      )}
    >
      {verdict}
    </span>
  )
}

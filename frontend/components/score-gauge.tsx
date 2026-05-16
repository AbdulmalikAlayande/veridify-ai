import { cn } from "@/lib/utils"

export function ScoreGauge({
  score,
  className,
}: {
  score: number
  className?: string
}) {
  const clampedScore = Math.max(0, Math.min(100, score))
  const stroke = clampedScore >= 70 ? "var(--color-chart-1)" : clampedScore >= 35 ? "var(--color-chart-2)" : "var(--color-destructive)"
  const circumference = 2 * Math.PI * 52
  const dashOffset = circumference * (1 - clampedScore / 100)

  return (
    <div className={cn("relative flex size-52 items-center justify-center", className)}>
      <svg viewBox="0 0 140 140" className="size-full -rotate-90">
        <circle cx="70" cy="70" r="52" fill="none" stroke="rgb(219 224 210 / 0.85)" strokeWidth="14" />
        <circle
          cx="70"
          cy="70"
          r="52"
          fill="none"
          stroke={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          strokeWidth="14"
        />
      </svg>
      <div className="absolute text-center">
        <p className="section-kicker">Trust score</p>
        <p className="font-heading text-5xl">{clampedScore}</p>
        <p className="text-sm text-muted-foreground">out of 100</p>
      </div>
    </div>
  )
}

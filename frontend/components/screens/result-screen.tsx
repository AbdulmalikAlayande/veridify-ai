"use client"

import Link from "next/link"
import { ArrowRightIcon, BadgeInfoIcon, ScaleIcon } from "lucide-react"
import { ScoreGauge } from "@/components/score-gauge"
import { StatusBadge } from "@/components/status-badge"
import { useAppState } from "@/components/app-state-provider"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getVerificationExplanation } from "@/lib/mock-data"
import { formatNaira } from "@/lib/utils"

export function ResultScreen() {
  const { latestVerification } = useAppState()

  if (!latestVerification) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No verification result yet</CardTitle>
          <CardDescription>Run a verification first so the result screen has something meaningful to show.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/verify">Go to verify</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <Card className="bg-white/85">
        <CardHeader className="items-center text-center">
          <p className="section-kicker">Screen 4 of 5</p>
          <CardTitle className="font-heading text-4xl">Result page</CardTitle>
          <CardDescription>The judge-facing verdict lives here, so the visual hierarchy needs to be immediate.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-6">
          <ScoreGauge score={latestVerification.trustScore} />
          <StatusBadge verdict={latestVerification.verdict} className="text-sm" />
          <div className="text-center">
            <p className="text-sm uppercase tracking-[0.24em] text-muted-foreground">Confidence</p>
            <p className="mt-2 font-heading text-3xl">{latestVerification.confidence}</p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card className="bg-white/85">
          <CardHeader>
            <CardTitle className="font-heading text-3xl">{latestVerification.imageName}</CardTitle>
            <CardDescription>{getVerificationExplanation(latestVerification.verdict)}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[24px] bg-secondary p-5">
              <p className="section-kicker">Charge</p>
              <p className="mt-3 font-heading text-4xl">{formatNaira(latestVerification.billedNaira)}</p>
              <p className="mt-2 text-sm text-muted-foreground">Deducted from the client balance for this verification.</p>
            </div>
            <div className="rounded-[24px] bg-primary p-5 text-primary-foreground">
              <p className="section-kicker text-primary-foreground/75">Remaining balance</p>
              <p className="mt-3 font-heading text-4xl">{formatNaira(latestVerification.balanceRemaining)}</p>
              <p className="mt-2 text-sm text-primary-foreground/75">Visible wallet state after the transaction completes.</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/85">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ScaleIcon className="size-5 text-primary" />
              <CardTitle>Signal breakdown</CardTitle>
            </div>
            <CardDescription>The UI leaves room for both spatial and frequency branches of the model story.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              ["Spatial score", latestVerification.breakdown.spatialScore],
              ["Frequency score", latestVerification.breakdown.frequencyScore],
            ].map(([label, value]) => (
              <div key={label} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>{label}</span>
                  <span className="font-semibold">{value}</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${value}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-white/85">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BadgeInfoIcon className="size-5 text-primary" />
              <CardTitle>Result notes</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <p>Processing time: {(latestVerification.processingMs / 1000).toFixed(2)}s</p>
            <p>{latestVerification.cached ? "This result reused a cached image hash." : "This result came from a fresh verification run."}</p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button asChild className="flex-1">
                <Link href="/verify">
                  Verify another image
                  <ArrowRightIcon className="size-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" className="flex-1">
                <Link href="/transactions">View transaction history</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

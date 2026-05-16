"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import {
  ArrowRightIcon,
  AtSignIcon,
  BadgeCheckIcon,
  Building2Icon,
  CheckIcon,
  CircleAlertIcon,
  ScanSearchIcon,
  ShieldCheckIcon,
  SparklesIcon,
  WalletCardsIcon,
  ZapIcon,
} from "lucide-react"
import { useAppState } from "@/components/app-state-provider"
import { CopyField } from "@/components/copy-field"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MockApiError } from "@/lib/api"
import { cn } from "@/lib/utils"

const features = [
  {
    icon: ShieldCheckIcon,
    title: "Onboard instantly",
    body: "Capture client name, email, virtual account details, and API key handoff in one motion.",
    tint: "from-emerald-200/70 to-emerald-100/40 text-emerald-700",
  },
  {
    icon: WalletCardsIcon,
    title: "Show the money trail",
    body: "Balance changes, top-ups, and verification charges stay visible for judges and internal demos.",
    tint: "from-amber-200/70 to-amber-100/40 text-amber-700",
  },
  {
    icon: BadgeCheckIcon,
    title: "Mock with discipline",
    body: "The interface mirrors the backend contract, so swapping to live endpoints stays low-risk.",
    tint: "from-sky-200/70 to-sky-100/40 text-sky-700",
  },
] as const

const stats = [
  { label: "Avg. verification", value: "<2s" },
  { label: "Mocked endpoints", value: "100%" },
  { label: "Setup steps", value: "1" },
] as const

const perks = [
  "Virtual account + API key generated for you",
  "Wallet, verification flow, and audit log linked",
  "Swap to the real backend without UI changes",
] as const

export function OnboardingScreen() {
  const router = useRouter()
  const { snapshot, createAccount, resetWorkspace, isBusy, isHydrated } = useAppState()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    try {
      await createAccount({ name, email })
      router.push("/dashboard")
    } catch (cause) {
      if (cause instanceof MockApiError) {
        setError(cause.message)
        return
      }

      setError("We could not create the workspace just yet.")
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 py-4 sm:px-6 lg:px-8">
      <div className="app-frame grid flex-1 overflow-hidden lg:grid-cols-[1.05fr_0.95fr]">
        {/* Hero panel */}
        <section className="relative overflow-hidden px-6 py-10 sm:px-10 lg:px-14 lg:py-14">
          <div className="pointer-events-none absolute -top-32 -left-24 size-[28rem] rounded-full bg-[radial-gradient(circle,oklch(0.78_0.18_150/0.55),transparent_70%)] blur-2xl float-orb" />
          <div className="pointer-events-none absolute top-10 right-[-6rem] size-[22rem] rounded-full bg-[radial-gradient(circle,oklch(0.80_0.16_70/0.5),transparent_70%)] blur-2xl float-orb-delayed" />
          <div className="pointer-events-none absolute right-12 bottom-[-6rem] size-[18rem] rounded-full bg-[radial-gradient(circle,oklch(0.74_0.16_220/0.35),transparent_70%)] blur-2xl float-orb" />

          <div className="relative flex h-full flex-col">
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/75 px-3 py-1.5 text-sm font-medium shadow-sm backdrop-blur">
                <span className="flex size-7 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-inner shadow-primary/40">
                  <ScanSearchIcon className="size-4" />
                </span>
                Veridify AI
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200/70 bg-emerald-50/80 px-3 py-1.5 text-xs font-semibold text-emerald-700 shadow-sm">
                <span className="relative flex size-2">
                  <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-500/60" />
                  <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
                </span>
                Live demo · mock mode
              </span>
            </div>

            <p className="section-kicker mt-10">Veridify launchpad</p>
            <h1 className="mt-4 max-w-2xl font-heading text-5xl leading-[0.95] sm:text-6xl">
              Build the <span className="gradient-text">trust layer</span> before the backend catches up.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-muted-foreground">
              This frontend already stitches onboarding, funding, verification, and audit history into one flow,
              so we can design the product experience now and drop the real API in later.
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {features.map(({ icon: Icon, title, body, tint }) => (
                <Card
                  key={title}
                  className="group/feature relative overflow-hidden border-white/60 bg-white/85 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/10"
                >
                  <div className={cn("pointer-events-none absolute inset-x-0 -top-12 h-24 bg-gradient-to-b opacity-60 blur-2xl transition-opacity group-hover/feature:opacity-90", tint)} />
                  <CardHeader>
                    <span className={cn("icon-chip bg-gradient-to-br", tint)}>
                      <Icon className="size-5" />
                    </span>
                    <CardTitle className="mt-2 text-base">{title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground">{body}</CardContent>
                </Card>
              ))}
            </div>

            <div className="mt-auto pt-10">
              <div className="flex flex-wrap items-center gap-x-8 gap-y-4 rounded-2xl border border-white/60 bg-white/55 px-5 py-4 backdrop-blur">
                {stats.map((stat, index) => (
                  <div key={stat.label} className="flex items-center gap-4">
                    {index > 0 ? <span className="hidden h-8 w-px bg-border/80 sm:block" /> : null}
                    <div>
                      <p className="font-heading text-2xl leading-none">{stat.value}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-muted-foreground">{stat.label}</p>
                    </div>
                  </div>
                ))}
                <div className="ml-auto hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
                  <ZapIcon className="size-3.5 text-primary" />
                  Real-time wallet sync
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Action panel */}
        <section className="relative border-t border-white/60 bg-gradient-to-b from-white/80 via-white/65 to-white/55 px-6 py-10 sm:px-10 lg:border-t-0 lg:border-l lg:px-12 lg:py-14">
          {snapshot.account ? (
            <Card className="relative overflow-hidden bg-white/90">
              <div className="pointer-events-none absolute inset-x-0 -top-16 h-32 bg-gradient-to-b from-primary/20 to-transparent blur-2xl" />
              <CardHeader className="relative">
                <div className="flex items-center gap-2">
                  <span className="inline-flex size-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 ring-4 ring-emerald-50">
                    <BadgeCheckIcon className="size-5" />
                  </span>
                  <p className="section-kicker">Workspace ready</p>
                </div>
                <CardTitle className="mt-3 font-heading text-3xl">{snapshot.account.name}</CardTitle>
                <CardDescription>
                  The synced frontend state is already active. You can jump straight into funding and verification.
                </CardDescription>
              </CardHeader>
              <CardContent className="relative space-y-4">
                <CopyField
                  label="Virtual account"
                  value={`${snapshot.account.squadVirtualAccount.accountNumber} — ${snapshot.account.squadVirtualAccount.bankName}`}
                />
                <CopyField label="API key" value={snapshot.account.apiKey} mono />
                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button asChild className="flex-1">
                    <Link href="/dashboard">
                      Continue to dashboard
                      <ArrowRightIcon className="size-4" />
                    </Link>
                  </Button>
                  <Button variant="outline" className="flex-1" onClick={resetWorkspace}>
                    Reset workspace
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="relative overflow-hidden bg-white/90">
              <div className="pointer-events-none absolute inset-x-0 -top-20 h-36 bg-gradient-to-b from-primary/15 via-amber-200/15 to-transparent blur-2xl" />
              <CardHeader className="relative">
                <div className="flex items-center justify-between gap-3">
                  <p className="section-kicker">Screen 1 of 5</p>
                  <div className="flex items-center gap-1.5" aria-hidden="true">
                    {[0, 1, 2, 3, 4].map((index) => (
                      <span
                        key={index}
                        className={cn(
                          "h-1.5 rounded-full transition-all",
                          index === 0 ? "w-6 bg-primary" : "w-1.5 bg-border",
                        )}
                      />
                    ))}
                  </div>
                </div>
                <CardTitle className="mt-3 font-heading text-3xl">Create the client workspace</CardTitle>
                <CardDescription>
                  This form becomes the entry point for the full demo flow: account creation, virtual account
                  display, API key reveal, and first navigation into the dashboard.
                </CardDescription>
              </CardHeader>
              <CardContent className="relative">
                <form className="space-y-5" onSubmit={handleSubmit}>
                  <div className="space-y-2">
                    <Label htmlFor="name">
                      <Building2Icon className="size-3.5 text-muted-foreground" />
                      Client name
                    </Label>
                    <div className="relative">
                      <Building2Icon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="name"
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        placeholder="Sterling Assurance"
                        autoComplete="organization"
                        className="h-11 rounded-xl pl-9"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">
                      <AtSignIcon className="size-3.5 text-muted-foreground" />
                      Work email
                    </Label>
                    <div className="relative">
                      <AtSignIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        placeholder="ops@sterling.ng"
                        autoComplete="email"
                        className="h-11 rounded-xl pl-9"
                      />
                    </div>
                  </div>

                  {error ? (
                    <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                      <CircleAlertIcon className="mt-0.5 size-4 shrink-0" />
                      <p>{error}</p>
                    </div>
                  ) : null}

                  <Button
                    type="submit"
                    size="lg"
                    className="h-11 w-full rounded-xl text-sm shadow-lg shadow-primary/20 transition-shadow hover:shadow-primary/30"
                    disabled={isBusy || !isHydrated}
                  >
                    {isBusy ? "Creating workspace..." : "Create account and continue"}
                    <ArrowRightIcon className="size-4 transition-transform group-hover/button:translate-x-0.5" />
                  </Button>
                </form>

                <div className="mt-7 rounded-2xl border border-dashed border-border/70 bg-muted/30 p-4">
                  <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    <SparklesIcon className="size-3.5 text-primary" />
                    What you get
                  </p>
                  <ul className="mt-3 space-y-2 text-sm">
                    {perks.map((perk) => (
                      <li key={perk} className="flex items-start gap-2">
                        <span className="mt-0.5 inline-flex size-4 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                          <CheckIcon className="size-3" />
                        </span>
                        <span className="text-muted-foreground">{perk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </main>
  )
}

"use client"

import Link from "next/link"
import { useState } from "react"
import {
  ArrowDownLeftIcon,
  ArrowRightIcon,
  ArrowUpRightIcon,
  CheckCircle2Icon,
  CircleAlertIcon,
  CoinsIcon,
  CreditCardIcon,
  HistoryIcon,
  KeyRoundIcon,
  ReceiptIcon,
  ScanSearchIcon,
  SparklesIcon,
  TrendingUpIcon,
  WalletCardsIcon,
} from "lucide-react"
import { useAppState } from "@/components/app-state-provider"
import { CopyField } from "@/components/copy-field"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MockApiError } from "@/lib/api"
import { cn } from "@/lib/utils"

function formatCurrency(amount: number) {
  return `N${amount.toLocaleString()}`
}

function formatRelative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.round(diff / 60000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

const quickActions = [
  {
    href: "/verify",
    title: "Verify an image",
    body: "Run a fresh image through the mocked spatial + frequency checks.",
    icon: ScanSearchIcon,
    accent: "from-emerald-200/70 to-emerald-100/30 text-emerald-700",
  },
  {
    href: "/transactions",
    title: "Open audit table",
    body: "Filter verifications by verdict and see who got charged when.",
    icon: HistoryIcon,
    accent: "from-sky-200/70 to-sky-100/30 text-sky-700",
  },
  {
    href: "/result",
    title: "Review latest result",
    body: "Jump back into the judge-facing verdict screen.",
    icon: SparklesIcon,
    accent: "from-amber-200/70 to-amber-100/30 text-amber-700",
  },
] as const

export function DashboardScreen() {
  const { snapshot, fundAccount, isBusy, verificationCostNaira } = useAppState()
  const [amount, setAmount] = useState("10000")
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!snapshot.account) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Start with onboarding</CardTitle>
          <CardDescription>Create an account first so the dashboard has a client to sync against.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/">Go to onboarding</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  async function handleFund(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage(null)
    setError(null)

    try {
      const result = await fundAccount({ amountNaira: Number(amount) })
      setMessage(`${result.message} Payment link: ${result.paymentLink}`)
    } catch (cause) {
      if (cause instanceof MockApiError) {
        setError(cause.message)
        return
      }

      setError("Funding could not be completed.")
    }
  }

  const verifications = snapshot.verifications.length
  const debits = snapshot.transactions.filter((transaction) => transaction.type === "DEBIT").length

  return (
    <div className="space-y-6">
      {/* Hero header */}
      <section className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <Card className="relative overflow-hidden bg-white/85">
          <div className="pointer-events-none absolute -top-24 -left-16 size-[22rem] rounded-full bg-[radial-gradient(circle,oklch(0.78_0.18_150/0.45),transparent_70%)] blur-2xl float-orb" />
          <div className="pointer-events-none absolute -top-16 right-[-4rem] size-[18rem] rounded-full bg-[radial-gradient(circle,oklch(0.80_0.16_70/0.4),transparent_70%)] blur-2xl float-orb-delayed" />
          <CardHeader className="relative">
            <div className="flex items-center justify-between gap-3">
              <p className="section-kicker">Screen 2 of 5</p>
              <div className="flex items-center gap-1.5" aria-hidden="true">
                {[0, 1, 2, 3, 4].map((index) => (
                  <span
                    key={index}
                    className={cn(
                      "h-1.5 rounded-full transition-all",
                      index === 1 ? "w-6 bg-primary" : index < 1 ? "w-1.5 bg-primary/40" : "w-1.5 bg-border",
                    )}
                  />
                ))}
              </div>
            </div>
            <CardTitle className="mt-3 font-heading text-4xl">
              <span className="gradient-text">Dashboard</span> home
            </CardTitle>
            <CardDescription>
              The product heartbeat lives here: balance, recent activity, and the next best action.
            </CardDescription>
          </CardHeader>
          <CardContent className="relative grid gap-4 md:grid-cols-3">
            {/* Balance tile */}
            <div className="relative overflow-hidden rounded-[22px] bg-gradient-to-br from-primary via-primary to-emerald-700 p-5 text-primary-foreground shadow-lg shadow-primary/25">
              <div className="pointer-events-none absolute -top-10 -right-8 size-32 rounded-full bg-white/20 blur-2xl" />
              <div className="relative flex items-center justify-between">
                <p className="text-sm text-primary-foreground/80">Balance</p>
                <span className="inline-flex size-9 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
                  <WalletCardsIcon className="size-4" />
                </span>
              </div>
              <p className="relative mt-3 font-heading text-4xl">{formatCurrency(snapshot.account.balanceNaira)}</p>
              <p className="relative mt-2 inline-flex items-center gap-1 text-xs text-primary-foreground/75">
                <TrendingUpIcon className="size-3" />
                Wallet synced in real time
              </p>
            </div>

            {/* Verifications tile */}
            <div className="relative overflow-hidden rounded-[22px] bg-secondary p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">Verifications</p>
                <span className="icon-chip bg-gradient-to-br from-sky-200/70 to-sky-100/40 text-sky-700">
                  <ScanSearchIcon className="size-4" />
                </span>
              </div>
              <p className="mt-3 font-heading text-4xl">{verifications}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                {verifications === 0 ? "No checks yet — run your first verification." : `${debits} charge${debits === 1 ? "" : "s"} recorded`}
              </p>
            </div>

            {/* Cost tile */}
            <div className="relative overflow-hidden rounded-[22px] bg-accent p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">Cost per check</p>
                <span className="icon-chip bg-gradient-to-br from-amber-200/70 to-amber-100/40 text-amber-700">
                  <ReceiptIcon className="size-4" />
                </span>
              </div>
              <p className="mt-3 font-heading text-4xl">{formatCurrency(verificationCostNaira)}</p>
              <p className="mt-2 text-xs text-muted-foreground">Flat charge per verification request</p>
            </div>
          </CardContent>
        </Card>

        {/* Quick actions */}
        <Card className="bg-white/85">
          <CardHeader>
            <p className="section-kicker">Quick actions</p>
            <CardTitle className="font-heading text-2xl">Keep the demo moving</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {quickActions.map(({ href, title, body, icon: Icon, accent }) => (
              <Link
                key={href}
                href={href}
                className="group/action flex items-center gap-3 rounded-2xl border border-transparent bg-white/60 p-3 transition-all hover:-translate-y-px hover:border-primary/30 hover:bg-white hover:shadow-md hover:shadow-primary/10"
              >
                <span className={cn("icon-chip shrink-0 bg-gradient-to-br", accent)}>
                  <Icon className="size-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{title}</p>
                  <p className="truncate text-xs text-muted-foreground">{body}</p>
                </div>
                <ArrowRightIcon className="size-4 text-muted-foreground transition-all group-hover/action:translate-x-0.5 group-hover/action:text-primary" />
              </Link>
            ))}
          </CardContent>
        </Card>
      </section>

      {/* Funding + activity */}
      <section className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <Card className="relative overflow-hidden bg-white/85">
          <div className="pointer-events-none absolute inset-x-0 -top-16 h-32 bg-gradient-to-b from-primary/15 to-transparent blur-2xl" />
          <CardHeader className="relative">
            <p className="section-kicker">Funding</p>
            <CardTitle className="font-heading text-2xl">Top up the verification wallet</CardTitle>
            <CardDescription>
              In live mode this comes from Squad. For now the UI simulates the webhook-confirmed credit instantly.
            </CardDescription>
          </CardHeader>
          <CardContent className="relative space-y-4">
            <form className="space-y-4" onSubmit={handleFund}>
              <div className="space-y-2">
                <Label htmlFor="fund-amount">
                  <CoinsIcon className="size-3.5 text-muted-foreground" />
                  Amount in naira
                </Label>
                <div className="relative">
                  <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-sm font-semibold text-muted-foreground">
                    N
                  </span>
                  <Input
                    id="fund-amount"
                    type="number"
                    min={100}
                    max={1000000}
                    step={100}
                    value={amount}
                    onChange={(event) => setAmount(event.target.value)}
                    className="h-11 rounded-xl pl-8 font-heading text-lg"
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {["5000", "10000", "25000"].map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setAmount(preset)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-medium transition-all",
                      amount === preset
                        ? "border-primary bg-primary text-primary-foreground shadow-sm"
                        : "border-border bg-white/70 text-muted-foreground hover:border-primary/40 hover:text-foreground",
                    )}
                  >
                    N{Number(preset).toLocaleString()}
                  </button>
                ))}
              </div>
              <Button
                type="submit"
                size="lg"
                className="h-11 w-full rounded-xl shadow-lg shadow-primary/20 transition-shadow hover:shadow-primary/30"
                disabled={isBusy}
              >
                {isBusy ? "Funding..." : "Fund account"}
                <CreditCardIcon className="size-4" />
              </Button>
            </form>

            {message ? (
              <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-700">
                <CheckCircle2Icon className="mt-0.5 size-4 shrink-0" />
                <p>{message}</p>
              </div>
            ) : null}
            {error ? (
              <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700">
                <CircleAlertIcon className="mt-0.5 size-4 shrink-0" />
                <p>{error}</p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="bg-white/85">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="section-kicker">Recent activity</p>
                <CardTitle className="font-heading text-2xl">Transaction pulse</CardTitle>
              </div>
              <Button asChild variant="ghost" size="sm" className="text-muted-foreground">
                <Link href="/transactions">
                  View all
                  <ArrowRightIcon className="size-3.5" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {snapshot.transactions.length === 0 ? (
              <div className="flex flex-col items-center gap-3 rounded-[22px] border border-dashed border-border bg-muted/30 p-8 text-center">
                <span className="icon-chip bg-gradient-to-br from-amber-200/70 to-amber-100/40 text-amber-700">
                  <CoinsIcon className="size-4" />
                </span>
                <p className="text-sm font-medium">No wallet movement yet</p>
                <p className="max-w-xs text-xs text-muted-foreground">
                  Fund the account to create the first visible transaction for the demo.
                </p>
              </div>
            ) : (
              snapshot.transactions.slice(0, 5).map((transaction) => {
                const isCredit = transaction.type === "CREDIT"
                return (
                  <div
                    key={transaction.id}
                    className="flex items-center gap-3 rounded-2xl border border-white/70 bg-white/75 p-3 transition-colors hover:border-primary/30 hover:bg-white"
                  >
                    <span
                      className={cn(
                        "icon-chip shrink-0",
                        isCredit
                          ? "bg-gradient-to-br from-emerald-200/70 to-emerald-100/40 text-emerald-700"
                          : "bg-gradient-to-br from-rose-200/70 to-rose-100/40 text-rose-700",
                      )}
                    >
                      {isCredit ? <ArrowDownLeftIcon className="size-4" /> : <ArrowUpRightIcon className="size-4" />}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{transaction.description}</p>
                      <p className="text-xs text-muted-foreground">{formatRelative(transaction.createdAt)}</p>
                    </div>
                    <div className="text-right">
                      <p className={cn("text-sm font-semibold", isCredit ? "text-emerald-700" : "text-foreground")}>
                        {isCredit ? "+" : "-"}
                        {formatCurrency(Math.abs(transaction.amountNaira))}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatCurrency(transaction.balanceAfter)} left
                      </p>
                    </div>
                  </div>
                )
              })
            )}
          </CardContent>
        </Card>
      </section>

      {/* Account details */}
      <section className="grid gap-4 md:grid-cols-2">
        <Card className="relative overflow-hidden bg-white/85">
          <div className="pointer-events-none absolute -top-10 right-[-3rem] size-40 rounded-full bg-[radial-gradient(circle,oklch(0.80_0.16_70/0.35),transparent_70%)] blur-2xl" />
          <CardHeader className="relative">
            <span className="icon-chip bg-gradient-to-br from-amber-200/70 to-amber-100/40 text-amber-700">
              <CoinsIcon className="size-4" />
            </span>
            <CardTitle className="mt-2">Virtual account</CardTitle>
            <CardDescription>Display this during the payment story of the demo.</CardDescription>
          </CardHeader>
          <CardContent className="relative space-y-3">
            <CopyField label="Account number" value={snapshot.account.squadVirtualAccount.accountNumber} />
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-border/70 bg-white/70 p-4">
                <p className="section-kicker">Bank</p>
                <p className="mt-2 text-sm font-semibold">{snapshot.account.squadVirtualAccount.bankName}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-white/70 p-4">
                <p className="section-kicker">Account name</p>
                <p className="mt-2 text-sm font-semibold">{snapshot.account.squadVirtualAccount.accountName}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden bg-white/85">
          <div className="pointer-events-none absolute -top-10 right-[-3rem] size-40 rounded-full bg-[radial-gradient(circle,oklch(0.78_0.18_150/0.3),transparent_70%)] blur-2xl" />
          <CardHeader className="relative">
            <span className="icon-chip bg-gradient-to-br from-emerald-200/70 to-emerald-100/40 text-emerald-700">
              <KeyRoundIcon className="size-4" />
            </span>
            <CardTitle className="mt-2">API key handoff</CardTitle>
            <CardDescription>Useful for Postman demos and for showing the product is API-first.</CardDescription>
          </CardHeader>
          <CardContent className="relative">
            <CopyField label="Secret key" value={snapshot.account.apiKey} mono />
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { PanelLeftIcon, ScanSearchIcon, WalletCardsIcon } from "lucide-react"
import { useAppState } from "@/components/app-state-provider"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { cn, formatNaira } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/verify", label: "Verify" },
  { href: "/result", label: "Result" },
  { href: "/transactions", label: "Transactions" },
]

function NavigationLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()

  return (
    <nav className="flex flex-col gap-2">
      {navItems.map((item) => {
        const active = pathname === item.href

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-white/60 hover:text-foreground",
            )}
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { snapshot, apiMode } = useAppState()

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 py-4 sm:px-6 lg:px-8">
      <div className="app-frame ambient-grid flex min-h-[calc(100vh-2rem)] flex-col overflow-hidden">
        <header className="border-b border-white/60 px-4 py-4 sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
                <ScanSearchIcon className="size-5" />
              </div>
              <div>
                <p className="section-kicker">Veridify Control Room</p>
                <h1 className="font-heading text-2xl leading-none">Media integrity, one flow</h1>
              </div>
            </div>

            <div className="hidden items-center gap-3 md:flex">
              <div className="rounded-full border border-white/70 bg-white/70 px-4 py-2 text-sm shadow-sm">
                <span className="text-muted-foreground">Mode</span>{" "}
                <span className="font-semibold text-foreground">{apiMode}</span>
              </div>
              {snapshot.account ? (
                <div className="rounded-full border border-white/70 bg-white/75 px-4 py-2 text-sm shadow-sm">
                  <span className="text-muted-foreground">{snapshot.account.name}</span>{" "}
                  <span className="font-semibold text-foreground">
                    {formatNaira(snapshot.account.balanceNaira)}
                  </span>
                </div>
              ) : null}
            </div>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon-sm" className="md:hidden">
                  <PanelLeftIcon />
                  <span className="sr-only">Open navigation</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[88vw] max-w-sm">
                <SheetHeader>
                  <SheetTitle>Workspace</SheetTitle>
                  <SheetDescription>Jump between onboarding, verification, and audit screens.</SheetDescription>
                </SheetHeader>
                <div className="px-4">
                  <NavigationLinks />
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </header>

        <div className="flex flex-1">
          <aside className="hidden w-72 flex-col border-r border-white/60 bg-white/35 px-5 py-6 md:flex">
            <NavigationLinks />

            <div className="mt-6 rounded-[24px] border border-white/70 bg-white/70 p-4 shadow-sm">
              <p className="section-kicker">Account Pulse</p>
              {snapshot.account ? (
                <>
                  <h2 className="mt-2 font-heading text-xl">{snapshot.account.name}</h2>
                  <p className="mt-2 text-sm text-muted-foreground">{snapshot.account.email}</p>
                  <div className="mt-4 flex items-center gap-3 rounded-2xl bg-primary/10 p-3">
                    <WalletCardsIcon className="size-4 text-primary" />
                    <div>
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Balance</p>
                      <p className="font-semibold">{formatNaira(snapshot.account.balanceNaira)}</p>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <h2 className="mt-2 font-heading text-xl">No client profile yet</h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Start on the onboarding screen, create an account, then the workspace will sync itself.
                  </p>
                  <Button asChild className="mt-4 w-full">
                    <Link href="/">Go to onboarding</Link>
                  </Button>
                </>
              )}
            </div>
          </aside>

          <main className="flex-1 px-4 py-5 sm:px-6 sm:py-6">{children}</main>
        </div>
      </div>
    </div>
  )
}

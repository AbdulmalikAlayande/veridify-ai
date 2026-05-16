"use client"

import Link from "next/link"
import { useDeferredValue, useState } from "react"
import { FilterIcon } from "lucide-react"
import { useAppState } from "@/components/app-state-provider"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { StatusBadge } from "@/components/status-badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { VerificationFilter } from "@/lib/types"

function formatCurrency(amount: number) {
  return `N${amount.toLocaleString()}`
}

export function TransactionsScreen() {
  const { snapshot } = useAppState()
  const [filter, setFilter] = useState<VerificationFilter>("ALL")
  const deferredFilter = useDeferredValue(filter)

  if (!snapshot.account) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No account in session</CardTitle>
          <CardDescription>Onboard a client first so we have verification history to audit.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/">Go to onboarding</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  const filteredVerifications = snapshot.verifications.filter((verification) => {
    if (deferredFilter === "ALL") {
      return true
    }

    return verification.verdict === deferredFilter
  })

  return (
    <div className="space-y-6">
      <Card className="bg-white/85">
        <CardHeader className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="section-kicker">Screen 5 of 5</p>
            <CardTitle className="font-heading text-4xl">Transaction history</CardTitle>
            <CardDescription>
              Filterable verification history with charge visibility, verdict summaries, and timestamps.
            </CardDescription>
          </div>
          <div className="w-full max-w-56">
            <Select value={filter} onValueChange={(value) => setFilter(value as VerificationFilter)}>
              <SelectTrigger className="w-full">
                <FilterIcon className="size-4 text-muted-foreground" />
                <SelectValue placeholder="Filter by verdict" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All verdicts</SelectItem>
                <SelectItem value="AUTHENTIC">Authentic</SelectItem>
                <SelectItem value="MANIPULATED">Manipulated</SelectItem>
                <SelectItem value="SYNTHETIC">Synthetic</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-white/85">
          <CardHeader>
            <CardTitle>All verifications</CardTitle>
          </CardHeader>
          <CardContent className="font-heading text-4xl">{snapshot.verifications.length}</CardContent>
        </Card>
        <Card className="bg-white/85">
          <CardHeader>
            <CardTitle>Debits recorded</CardTitle>
          </CardHeader>
          <CardContent className="font-heading text-4xl">
            {snapshot.transactions.filter((transaction) => transaction.type === "DEBIT").length}
          </CardContent>
        </Card>
        <Card className="bg-white/85">
          <CardHeader>
            <CardTitle>Balance now</CardTitle>
          </CardHeader>
          <CardContent className="font-heading text-4xl">{formatCurrency(snapshot.account.balanceNaira)}</CardContent>
        </Card>
      </div>

      <Card className="bg-white/85">
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>File</TableHead>
                <TableHead>Verdict</TableHead>
                <TableHead>Trust score</TableHead>
                <TableHead>Amount billed</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredVerifications.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                    No verification rows match the current filter.
                  </TableCell>
                </TableRow>
              ) : (
                filteredVerifications.map((verification) => (
                  <TableRow key={verification.verificationId}>
                    <TableCell>{new Date(verification.createdAt).toLocaleString()}</TableCell>
                    <TableCell className="max-w-48 truncate">{verification.imageName}</TableCell>
                    <TableCell>
                      <StatusBadge verdict={verification.verdict} />
                    </TableCell>
                    <TableCell>{verification.trustScore}</TableCell>
                    <TableCell>{formatCurrency(verification.billedNaira)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

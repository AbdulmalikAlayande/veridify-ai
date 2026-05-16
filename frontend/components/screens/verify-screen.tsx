"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowRightIcon, ImagePlusIcon, LoaderCircleIcon, WalletCardsIcon } from "lucide-react"
import { useAppState } from "@/components/app-state-provider"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MockApiError } from "@/lib/api"

function formatCurrency(amount: number) {
  return `N${amount.toLocaleString()}`
}

export function VerifyScreen() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { snapshot, verifyImage, verificationCostNaira } = useAppState()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [timerMs, setTimerMs] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isProcessing) {
      return
    }

    const startedAt = Date.now()
    const intervalId = window.setInterval(() => {
      setTimerMs(Date.now() - startedAt)
    }, 90)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [isProcessing])

  if (!snapshot.account) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Create an account first</CardTitle>
          <CardDescription>The verify screen needs an account, balance, and API context.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/">Go to onboarding</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  async function handleVerify() {
    if (!selectedFile) {
      setError("Select an image before you run verification.")
      return
    }

    setError(null)
    setIsProcessing(true)
    setTimerMs(0)

    try {
      await verifyImage(selectedFile)
      router.push("/result")
    } catch (cause) {
      if (cause instanceof MockApiError) {
        setError(cause.message)
      } else {
        setError("Verification failed unexpectedly.")
      }
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <Card className="bg-white/85">
        <CardHeader>
          <p className="section-kicker">Screen 3 of 5</p>
          <CardTitle className="font-heading text-4xl">Verify page</CardTitle>
          <CardDescription>
            Upload the image, watch the processing state, then push the user into the result view without losing the
            financial context.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(event) => {
              event.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault()
              setIsDragging(false)
              const file = event.dataTransfer.files[0]
              if (file) {
                setSelectedFile(file)
              }
            }}
            className={`flex min-h-80 w-full flex-col items-center justify-center rounded-[32px] border-2 border-dashed px-6 text-center transition-colors ${
              isDragging ? "border-primary bg-primary/10" : "border-border bg-muted/35 hover:bg-muted/50"
            }`}
          >
            <ImagePlusIcon className="size-10 text-primary" />
            <p className="mt-4 font-heading text-3xl">Drop a suspicious image here</p>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              JPEG, PNG, or WEBP. The mock flow still follows the intended backend contract and charges the wallet.
            </p>
            {selectedFile ? (
              <div className="mt-6 rounded-full bg-white/80 px-4 py-2 text-sm font-medium shadow-sm">
                {selectedFile.name}
              </div>
            ) : null}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0] ?? null
              setSelectedFile(file)
            }}
          />

          {error ? <div className="rounded-2xl bg-rose-50 p-4 text-sm text-rose-700">{error}</div> : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button className="flex-1" onClick={handleVerify} disabled={isProcessing}>
              {isProcessing ? "Processing..." : "Submit for verification"}
              {isProcessing ? <LoaderCircleIcon className="size-4 animate-spin" /> : <ArrowRightIcon className="size-4" />}
            </Button>
            <Button variant="outline" className="flex-1" onClick={() => setSelectedFile(null)}>
              Clear selection
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card className="bg-white/85">
          <CardHeader>
            <WalletCardsIcon className="size-5 text-primary" />
            <CardTitle>Verification wallet</CardTitle>
            <CardDescription>Keep the cost visible so the payment story is always grounded.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[24px] bg-primary p-5 text-primary-foreground">
              <p className="text-sm text-primary-foreground/75">Current balance</p>
              <p className="mt-3 font-heading text-4xl">{formatCurrency(snapshot.account.balanceNaira)}</p>
            </div>
            <div className="rounded-[24px] bg-secondary p-5">
              <p className="text-sm text-muted-foreground">Charge per request</p>
              <p className="mt-3 font-heading text-4xl">{formatCurrency(verificationCostNaira)}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/85">
          <CardHeader>
            <CardTitle>Processing feedback</CardTitle>
            <CardDescription>The spinner and timer make the model work feel visible to a judge.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-[24px] border border-border/70 bg-muted/40 p-5">
              <p className="section-kicker">Elapsed time</p>
              <p className="mt-3 font-heading text-5xl">{(timerMs / 1000).toFixed(2)}s</p>
              <p className="mt-2 text-sm text-muted-foreground">
                {isProcessing
                  ? "Inference is running and the result page will update as soon as the decision lands."
                  : "The timer activates only while an image is being processed."}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

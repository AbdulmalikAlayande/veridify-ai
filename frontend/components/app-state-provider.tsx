"use client"

import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { createAccountRequest, fundAccountRequest, getApiMode, MockApiError, verifyImageRequest } from "@/lib/api"
import { createEmptySnapshot, STORAGE_KEY, VERIFICATION_COST_NAIRA } from "@/lib/mock-data"
import type {
  AppSnapshot,
  CreateAccountInput,
  FundAccountInput,
  VerificationRecord,
} from "@/lib/types"

interface AppStateContextValue {
  snapshot: AppSnapshot
  isHydrated: boolean
  isBusy: boolean
  apiMode: string
  latestVerification: VerificationRecord | null
  verificationCostNaira: number
  createAccount: (input: CreateAccountInput) => Promise<void>
  fundAccount: (input: FundAccountInput) => Promise<{ paymentLink: string; message: string }>
  verifyImage: (file: File) => Promise<VerificationRecord>
  resetWorkspace: () => void
}

const AppStateContext = createContext<AppStateContextValue | null>(null)

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<AppSnapshot>(createEmptySnapshot)
  const [isHydrated, setIsHydrated] = useState(false)
  const [isBusy, setIsBusy] = useState(false)

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY)
      if (saved) {
        setSnapshot(JSON.parse(saved) as AppSnapshot)
      }
    } finally {
      setIsHydrated(true)
    }
  }, [])

  useEffect(() => {
    if (!isHydrated) {
      return
    }

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot))
  }, [isHydrated, snapshot])

  const latestVerification =
    snapshot.verifications.find((item) => item.verificationId === snapshot.latestVerificationId) ?? null

  const value = useMemo<AppStateContextValue>(
    () => ({
      snapshot,
      isHydrated,
      isBusy,
      apiMode: getApiMode(),
      latestVerification,
      verificationCostNaira: VERIFICATION_COST_NAIRA,
      async createAccount(input) {
        setIsBusy(true)

        try {
          const nextSnapshot = await createAccountRequest(snapshot, input)
          startTransition(() => {
            setSnapshot(nextSnapshot)
          })
        } finally {
          setIsBusy(false)
        }
      },
      async fundAccount(input) {
        setIsBusy(true)

        try {
          const result = await fundAccountRequest(snapshot, input)
          startTransition(() => {
            setSnapshot(result.snapshot)
          })

          return {
            paymentLink: result.paymentLink,
            message: result.message,
          }
        } finally {
          setIsBusy(false)
        }
      },
      async verifyImage(file) {
        setIsBusy(true)

        try {
          const result = await verifyImageRequest(snapshot, file)
          startTransition(() => {
            setSnapshot(result.snapshot)
          })
          return result.verification
        } finally {
          setIsBusy(false)
        }
      },
      resetWorkspace() {
        const empty = createEmptySnapshot()
        startTransition(() => {
          setSnapshot(empty)
        })
        window.localStorage.removeItem(STORAGE_KEY)
      },
    }),
    [isBusy, isHydrated, latestVerification, snapshot],
  )

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>
}

export function useAppState() {
  const context = useContext(AppStateContext)

  if (!context) {
    throw new Error("useAppState must be used within AppStateProvider")
  }

  return context
}

export { MockApiError }

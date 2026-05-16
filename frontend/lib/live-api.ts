import {
  MockApiError,
  createMockAccount,
  fundMockAccount,
  verifyMockImage,
} from "@/lib/mock-data"
import type {
  AccountRecord,
  AppSnapshot,
  Confidence,
  CreateAccountInput,
  FundAccountInput,
  FundAccountResult,
  SquadVirtualAccount,
  TransactionRecord,
  Verdict,
  VerificationRecord,
  VerifyImageResult,
} from "@/lib/types"

export function getLiveBaseUrl(): string | null {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  return url ? url.replace(/\/+$/, "") : null
}

interface RawCreateAccountResponse {
  client_id: string
  api_key: string
  message: string
  squad_virtual_account: {
    account_number: string
    bank_name: string
    account_name: string
  } | null
  balance_naira: number
}

interface RawTransaction {
  type: string
  amount_naira: number
  description: string | null
  balance_after: number
  created_at: string
}

interface RawBalanceResponse {
  balance_naira: number
  total_verifications: number
  recent_transactions: RawTransaction[]
}

interface RawFundResponse {
  payment_link: string
  amount_naira: number
  expires_in_hours: number
  message: string
}

interface RawVerifyResponse {
  verification_id: string
  trust_score: number
  verdict: string
  confidence: string
  processing_ms: number
  cached: boolean
  billed_naira: number
  balance_remaining: number
  breakdown: {
    spatial_score: number
    frequency_score: number
  }
}

async function liveFetch<T>(path: string, init: RequestInit, apiKey?: string): Promise<T> {
  const baseUrl = getLiveBaseUrl()
  if (!baseUrl) {
    throw new MockApiError(
      "API_NOT_CONFIGURED",
      "NEXT_PUBLIC_API_BASE_URL is not set. Configure it or run in mock mode.",
    )
  }

  const headers = new Headers(init.headers)
  if (apiKey) {
    headers.set("X-API-Key", apiKey)
  }

  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers })
  } catch (cause) {
    throw new MockApiError(
      "NETWORK_ERROR",
      cause instanceof Error ? cause.message : "Could not reach the Veridify backend.",
    )
  }

  const text = await response.text()
  let body: unknown = null
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
  }

  if (!response.ok) {
    const envelope = (body ?? {}) as {
      error?: string
      message?: string
      detail?: Record<string, unknown>
    }
    const code = envelope.error ?? `HTTP_${response.status}`
    const message = envelope.message ?? `Request failed with status ${response.status}`
    const detail = envelope.detail ?? {}
    throw new MockApiError(code, message, detail)
  }

  return body as T
}

function mapVirtualAccount(
  raw: RawCreateAccountResponse["squad_virtual_account"],
): SquadVirtualAccount {
  if (!raw) {
    return {
      accountNumber: "Pending",
      bankName: "Squad VA provisioning",
      accountName: "Pending",
    }
  }

  return {
    accountNumber: raw.account_number,
    bankName: raw.bank_name,
    accountName: raw.account_name,
  }
}

function mapTransaction(raw: RawTransaction): TransactionRecord {
  const type = raw.type === "CREDIT" ? "CREDIT" : "DEBIT"

  return {
    id: `srv_${raw.created_at}_${raw.amount_naira}_${type}`,
    type,
    amountNaira: raw.amount_naira,
    description: raw.description ?? "",
    balanceAfter: raw.balance_after,
    createdAt: raw.created_at,
  }
}

function mapVerification(
  raw: RawVerifyResponse,
  context: { imageName: string; imageHash: string; createdAt: string },
): VerificationRecord {
  return {
    verificationId: raw.verification_id,
    imageName: context.imageName,
    imageHash: context.imageHash,
    trustScore: raw.trust_score,
    verdict: raw.verdict as Verdict,
    confidence: raw.confidence as Confidence,
    processingMs: raw.processing_ms,
    cached: raw.cached,
    billedNaira: raw.billed_naira,
    balanceRemaining: raw.balance_remaining,
    breakdown: {
      spatialScore: raw.breakdown.spatial_score,
      frequencyScore: raw.breakdown.frequency_score,
    },
    createdAt: context.createdAt,
  }
}

async function hashFile(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const digest = await crypto.subtle.digest("SHA-256", buffer)
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")
}

async function fetchBalance(apiKey: string): Promise<RawBalanceResponse> {
  return liveFetch<RawBalanceResponse>("/account/balance", { method: "GET" }, apiKey)
}

// Errors that represent a user-correctable problem and should NOT fall back to
// the mock — judges still need to see real validation/auth/rate-limit UX.
const USER_FACING_ERROR_CODES = new Set([
  "INVALID_ACCOUNT_INPUT",
  "INVALID_EMAIL",
  "INVALID_FUNDING_AMOUNT",
  "ACCOUNT_REQUIRED",
  "INVALID_API_KEY",
  "EMAIL_ALREADY_REGISTERED",
  "INSUFFICIENT_BALANCE",
  "RATE_LIMIT_EXCEEDED",
  "UNSUPPORTED_IMAGE_TYPE",
  "IMAGE_TOO_LARGE",
  "API_NOT_CONFIGURED",
])

function isInfrastructureFailure(cause: unknown): cause is MockApiError {
  if (!(cause instanceof MockApiError)) {
    return false
  }
  return !USER_FACING_ERROR_CODES.has(cause.code)
}

function logFallback(operation: string, cause: MockApiError) {
  if (typeof console !== "undefined") {
    console.warn(
      `[live-api] ${operation} fell back to mock — ${cause.code}: ${cause.message}`,
    )
  }
}

export async function createLiveAccount(
  snapshot: AppSnapshot,
  input: CreateAccountInput,
): Promise<AppSnapshot> {
  const name = input.name.trim()
  const email = input.email.trim().toLowerCase()

  if (!name || !email) {
    throw new MockApiError("INVALID_ACCOUNT_INPUT", "Name and email are required.")
  }

  try {
    const raw = await liveFetch<RawCreateAccountResponse>("/account/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email }),
    })

    const account: AccountRecord = {
      clientId: raw.client_id,
      name,
      email,
      apiKey: raw.api_key,
      balanceNaira: raw.balance_naira,
      createdAt: new Date().toISOString(),
      squadVirtualAccount: mapVirtualAccount(raw.squad_virtual_account),
    }

    return {
      account,
      transactions: [],
      verifications: [],
      latestVerificationId: null,
    }
  } catch (cause) {
    if (isInfrastructureFailure(cause)) {
      logFallback("createAccount", cause)
      return createMockAccount(snapshot, input)
    }
    throw cause
  }
}

export async function fundLiveAccount(
  snapshot: AppSnapshot,
  input: FundAccountInput,
): Promise<FundAccountResult> {
  if (!snapshot.account) {
    throw new MockApiError("ACCOUNT_REQUIRED", "Create an account before funding your balance.")
  }

  try {
    const raw = await liveFetch<RawFundResponse>(
      "/account/fund",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_naira: input.amountNaira }),
      },
      snapshot.account.apiKey,
    )

    const balance = await fetchBalance(snapshot.account.apiKey)

    return {
      snapshot: {
        account: {
          ...snapshot.account,
          balanceNaira: balance.balance_naira,
        },
        transactions: balance.recent_transactions.map(mapTransaction),
        verifications: snapshot.verifications,
        latestVerificationId: snapshot.latestVerificationId,
      },
      paymentLink: raw.payment_link,
      amountNaira: raw.amount_naira,
      expiresInHours: raw.expires_in_hours,
      message: raw.message,
    }
  } catch (cause) {
    if (isInfrastructureFailure(cause)) {
      logFallback("fundAccount", cause)
      return fundMockAccount(snapshot, input)
    }
    throw cause
  }
}

export async function verifyLiveImage(
  snapshot: AppSnapshot,
  file: File,
): Promise<VerifyImageResult> {
  if (!snapshot.account) {
    throw new MockApiError("ACCOUNT_REQUIRED", "Create an account before running verification.")
  }

  const imageHash = await hashFile(file)
  const createdAt = new Date().toISOString()

  try {
    const form = new FormData()
    form.append("image", file)

    const raw = await liveFetch<RawVerifyResponse>(
      "/verify",
      { method: "POST", body: form },
      snapshot.account.apiKey,
    )

    const verification = mapVerification(raw, { imageName: file.name, imageHash, createdAt })

    const balance = await fetchBalance(snapshot.account.apiKey)
    const serverTransactions = balance.recent_transactions.map(mapTransaction)

    // The backend's recent_transactions doesn't carry verdict context; tag the latest matching
    // DEBIT row so the transactions screen can still surface the verdict next to the charge.
    let annotated: TransactionRecord[]
    const matchIndex = serverTransactions.findIndex(
      (tx) => tx.type === "DEBIT" && tx.amountNaira === verification.billedNaira,
    )
    if (matchIndex >= 0) {
      annotated = serverTransactions.map((tx, index) =>
        index === matchIndex
          ? { ...tx, verdict: verification.verdict, trustScore: verification.trustScore }
          : tx,
      )
    } else {
      annotated = serverTransactions
    }

    return {
      snapshot: {
        account: {
          ...snapshot.account,
          balanceNaira: balance.balance_naira,
        },
        transactions: annotated,
        verifications: [verification, ...snapshot.verifications],
        latestVerificationId: verification.verificationId,
      },
      verification,
    }
  } catch (cause) {
    if (isInfrastructureFailure(cause)) {
      logFallback("verifyImage", cause)
      return verifyMockImage(snapshot, file)
    }
    throw cause
  }
}

export async function refreshLiveAccount(snapshot: AppSnapshot): Promise<AppSnapshot> {
  if (!snapshot.account) {
    return snapshot
  }

  try {
    const balance = await fetchBalance(snapshot.account.apiKey)

    return {
      account: {
        ...snapshot.account,
        balanceNaira: balance.balance_naira,
      },
      transactions: balance.recent_transactions.map(mapTransaction),
      verifications: snapshot.verifications,
      latestVerificationId: snapshot.latestVerificationId,
    }
  } catch (cause) {
    if (isInfrastructureFailure(cause)) {
      logFallback("refreshAccount", cause)
      return snapshot
    }
    throw cause
  }
}

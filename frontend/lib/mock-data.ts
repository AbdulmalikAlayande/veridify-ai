import type {
  AccountRecord,
  AppSnapshot,
  Confidence,
  CreateAccountInput,
  FundAccountInput,
  FundAccountResult,
  TransactionRecord,
  Verdict,
  VerificationRecord,
  VerifyImageResult,
} from "@/lib/types"
import { formatNaira } from "@/lib/utils"

export const VERIFICATION_COST_NAIRA = 175
export const STORAGE_KEY = "veridify-front-state"

export class MockApiError extends Error {
  code: string
  detail: Record<string, unknown>

  constructor(code: string, message: string, detail: Record<string, unknown> = {}) {
    super(message)
    this.code = code
    this.detail = detail
  }
}

export function createEmptySnapshot(): AppSnapshot {
  return {
    account: null,
    transactions: [],
    verifications: [],
    latestVerificationId: null,
  }
}

function generateId(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}${crypto.randomUUID()}`
  }

  return `${prefix}${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`
}

async function hashBytes(buffer: ArrayBuffer) {
  const digest = await crypto.subtle.digest("SHA-256", buffer)
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")
}

async function hashText(text: string) {
  const encoded = new TextEncoder().encode(text)
  return hashBytes(encoded.buffer)
}

function deriveVerdict(trustScore: number): { verdict: Verdict; confidence: Confidence } {
  if (trustScore >= 70) {
    const confidence: Confidence = trustScore >= 85 ? "HIGH" : trustScore >= 75 ? "MEDIUM" : "LOW"
    return { verdict: "AUTHENTIC", confidence }
  }

  if (trustScore >= 35) {
    const distanceFromCenter = Math.abs(trustScore - 52)
    const confidence: Confidence =
      distanceFromCenter <= 7 ? "HIGH" : distanceFromCenter <= 12 ? "MEDIUM" : "LOW"
    return { verdict: "MANIPULATED", confidence }
  }

  const confidence: Confidence = trustScore <= 15 ? "HIGH" : trustScore <= 25 ? "MEDIUM" : "LOW"
  return { verdict: "SYNTHETIC", confidence }
}

function delay(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}

function createPaymentLink(clientId: string, amountNaira: number) {
  return `https://pay.squadco.com/mock/${clientId}?amount=${amountNaira}`
}

function createVirtualAccount(signature: string, name: string): AccountRecord["squadVirtualAccount"] {
  const digits = Number.parseInt(signature.slice(0, 12), 16).toString().slice(0, 10).padStart(10, "3")

  return {
    accountNumber: digits,
    bankName: "GTBank Sandbox",
    accountName: `VERIDIFY/${name.toUpperCase()}`,
  }
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export async function createMockAccount(
  currentSnapshot: AppSnapshot,
  input: CreateAccountInput,
): Promise<AppSnapshot> {
  const name = input.name.trim()
  const email = input.email.trim().toLowerCase()

  if (!name || !email) {
    throw new MockApiError("INVALID_ACCOUNT_INPUT", "Name and email are required.")
  }

  if (!EMAIL_PATTERN.test(email)) {
    throw new MockApiError("INVALID_EMAIL", "Enter a valid work email address.")
  }

  await delay(650)

  const signature = await hashText(`${name}|${email}`)
  const account: AccountRecord = {
    clientId: generateId("client_"),
    name,
    email,
    apiKey: `vrf_sk_live_${signature.slice(0, 40)}`,
    balanceNaira: currentSnapshot.account?.balanceNaira ?? 0,
    createdAt: new Date().toISOString(),
    squadVirtualAccount: createVirtualAccount(signature, name),
  }

  return {
    account,
    transactions: currentSnapshot.transactions,
    verifications: currentSnapshot.verifications,
    latestVerificationId: currentSnapshot.latestVerificationId,
  }
}

export async function fundMockAccount(
  snapshot: AppSnapshot,
  input: FundAccountInput,
): Promise<FundAccountResult> {
  if (!snapshot.account) {
    throw new MockApiError("ACCOUNT_REQUIRED", "Create an account before funding your balance.")
  }

  if (input.amountNaira < 100 || input.amountNaira > 1_000_000) {
    throw new MockApiError(
      "INVALID_FUNDING_AMOUNT",
      "Funding amount must be between ₦100 and ₦1,000,000.",
    )
  }

  await delay(900)

  const balanceAfter = snapshot.account.balanceNaira + input.amountNaira
  const transaction: TransactionRecord = {
    id: generateId("txn_"),
    type: "CREDIT",
    amountNaira: input.amountNaira,
    description: `Squad top-up confirmed for ${formatNaira(input.amountNaira)}`,
    balanceAfter,
    createdAt: new Date().toISOString(),
  }

  return {
    snapshot: {
      account: {
        ...snapshot.account,
        balanceNaira: balanceAfter,
      },
      transactions: [transaction, ...snapshot.transactions],
      verifications: snapshot.verifications,
      latestVerificationId: snapshot.latestVerificationId,
    },
    paymentLink: createPaymentLink(snapshot.account.clientId, input.amountNaira),
    amountNaira: input.amountNaira,
    expiresInHours: 24,
    message: "Sandbox payment completed and balance credited instantly.",
  }
}

export async function verifyMockImage(snapshot: AppSnapshot, file: File): Promise<VerifyImageResult> {
  if (!snapshot.account) {
    throw new MockApiError("ACCOUNT_REQUIRED", "Create an account before running verification.")
  }

  if (snapshot.account.balanceNaira < VERIFICATION_COST_NAIRA) {
    throw new MockApiError("INSUFFICIENT_BALANCE", "Fund your account to continue verifications.", {
      balanceNaira: snapshot.account.balanceNaira,
      verificationCostNaira: VERIFICATION_COST_NAIRA,
      paymentLink: createPaymentLink(snapshot.account.clientId, 10_000),
    })
  }

  if (!file.type.startsWith("image/")) {
    throw new MockApiError("UNSUPPORTED_IMAGE_TYPE", "Only image files can be verified.")
  }

  const imageBuffer = await file.arrayBuffer()
  const imageHash = await hashBytes(imageBuffer)
  const cachedMatch = snapshot.verifications.find((item) => item.imageHash === imageHash)
  const seed = Number.parseInt(imageHash.slice(0, 8), 16) % 100
  const trustScore = cachedMatch?.trustScore ?? seed
  const { verdict, confidence } = deriveVerdict(trustScore)
  const processingMs = cachedMatch?.processingMs ?? (380 + (Number.parseInt(imageHash.slice(8, 12), 16) % 850))
  const spatialScore = cachedMatch?.breakdown.spatialScore ?? Math.min(100, trustScore + 6)
  const frequencyScore = cachedMatch?.breakdown.frequencyScore ?? Math.max(0, trustScore - 5)
  const balanceRemaining = snapshot.account.balanceNaira - VERIFICATION_COST_NAIRA

  await delay(cachedMatch ? 220 : processingMs)

  const verification: VerificationRecord = {
    verificationId: generateId("vrf_"),
    imageName: file.name,
    imageHash,
    trustScore,
    verdict,
    confidence,
    processingMs,
    cached: Boolean(cachedMatch),
    billedNaira: VERIFICATION_COST_NAIRA,
    balanceRemaining,
    breakdown: {
      spatialScore,
      frequencyScore,
    },
    createdAt: new Date().toISOString(),
  }

  const transaction: TransactionRecord = {
    id: generateId("txn_"),
    type: "DEBIT",
    amountNaira: VERIFICATION_COST_NAIRA,
    description: `${verdict} verdict for ${file.name}`,
    balanceAfter: balanceRemaining,
    createdAt: verification.createdAt,
    verdict,
    trustScore,
  }

  return {
    snapshot: {
      account: {
        ...snapshot.account,
        balanceNaira: balanceRemaining,
      },
      transactions: [transaction, ...snapshot.transactions],
      verifications: [verification, ...snapshot.verifications],
      latestVerificationId: verification.verificationId,
    },
    verification,
  }
}

export function getVerificationExplanation(verdict: Verdict) {
  if (verdict === "AUTHENTIC") {
    return "The image reads like a genuine capture with strong spatial and frequency consistency."
  }

  if (verdict === "MANIPULATED") {
    return "The image keeps some real-photo traits, but the signal suggests edits or compositing."
  }

  return "The patterning looks strongly synthetic, which usually points to AI generation rather than capture."
}

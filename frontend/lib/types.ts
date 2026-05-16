export type Verdict = "AUTHENTIC" | "MANIPULATED" | "SYNTHETIC"
export type Confidence = "HIGH" | "MEDIUM" | "LOW"
export type TransactionType = "CREDIT" | "DEBIT"
export type VerificationFilter = "ALL" | Verdict

export interface SquadVirtualAccount {
  accountNumber: string
  bankName: string
  accountName: string
}

export interface AccountRecord {
  clientId: string
  name: string
  email: string
  apiKey: string
  balanceNaira: number
  createdAt: string
  squadVirtualAccount: SquadVirtualAccount
}

export interface VerificationBreakdown {
  spatialScore: number
  frequencyScore: number
}

export interface VerificationRecord {
  verificationId: string
  imageName: string
  imageHash: string
  trustScore: number
  verdict: Verdict
  confidence: Confidence
  processingMs: number
  cached: boolean
  billedNaira: number
  balanceRemaining: number
  breakdown: VerificationBreakdown
  createdAt: string
}

export interface TransactionRecord {
  id: string
  type: TransactionType
  amountNaira: number
  description: string
  balanceAfter: number
  createdAt: string
  verdict?: Verdict
  trustScore?: number
}

export interface AppSnapshot {
  account: AccountRecord | null
  transactions: TransactionRecord[]
  verifications: VerificationRecord[]
  latestVerificationId: string | null
}

export interface CreateAccountInput {
  name: string
  email: string
}

export interface FundAccountInput {
  amountNaira: number
}

export interface FundAccountResult {
  snapshot: AppSnapshot
  paymentLink: string
  amountNaira: number
  expiresInHours: number
  message: string
}

export interface VerifyImageResult {
  snapshot: AppSnapshot
  verification: VerificationRecord
}

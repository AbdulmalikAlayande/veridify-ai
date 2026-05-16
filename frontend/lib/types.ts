export type Verdict = "AUTHENTIC" | "MANIPULATED" | "SYNTHETIC"
export type VerificationFilter = Verdict | "ALL"
export type TransactionType = "DEBIT" | "CREDIT"

export interface Account {
  accountId: string
  accountName: string
  balanceNaira: number
  createdAt: string
}

export interface VerificationRecord {
  verificationId: string
  imageName: string
  verdict: Verdict
  trustScore: number
  billedNaira: number
  createdAt: string
}

export interface Transaction {
  transactionId: string
  type: TransactionType
  amountNaira: number
  description: string
  createdAt: string
}

export interface AppSnapshot {
  account: Account | null
  verifications: VerificationRecord[]
  transactions: Transaction[]
  latestVerificationId: string | null
}

export interface CreateAccountInput {
  accountName: string
}

export interface FundAccountInput {
  amountNaira: number
}

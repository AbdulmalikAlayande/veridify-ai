import type {
  AppSnapshot,
  CreateAccountInput,
  FundAccountInput,
  VerificationRecord,
  Verdict,
} from "@/lib/types"
import { VERIFICATION_COST_NAIRA } from "@/lib/mock-data"

export class MockApiError extends Error {
  constructor(message: string, public code?: string) {
    super(message)
    this.name = "MockApiError"
  }
}

export function getApiMode(): string {
  return process.env.NEXT_PUBLIC_API_MODE || "mock"
}

function generateId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

function getRandomVerdict(): Verdict {
  const verdicts: Verdict[] = ["AUTHENTIC", "MANIPULATED", "SYNTHETIC"]
  return verdicts[Math.floor(Math.random() * verdicts.length)]
}

function getRandomTrustScore(): number {
  return Math.floor(Math.random() * 100)
}

export async function createAccountRequest(
  snapshot: AppSnapshot,
  input: CreateAccountInput,
): Promise<AppSnapshot> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 1000))

  if (!input.accountName || input.accountName.trim().length === 0) {
    throw new MockApiError("Account name is required", "INVALID_INPUT")
  }

  const newAccount = {
    accountId: generateId("acc"),
    accountName: input.accountName,
    balanceNaira: 10000, // Initial balance
    createdAt: new Date().toISOString(),
  }

  return {
    ...snapshot,
    account: newAccount,
    transactions: [
      ...snapshot.transactions,
      {
        transactionId: generateId("txn"),
        type: "CREDIT" as const,
        amountNaira: 10000,
        description: "Account creation bonus",
        createdAt: new Date().toISOString(),
      },
    ],
  }
}

export async function fundAccountRequest(
  snapshot: AppSnapshot,
  input: FundAccountInput,
): Promise<{
  snapshot: AppSnapshot
  paymentLink: string
  message: string
}> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 1500))

  if (!snapshot.account) {
    throw new MockApiError("No account found in session", "NO_ACCOUNT")
  }

  if (!input.amountNaira || input.amountNaira <= 0) {
    throw new MockApiError("Amount must be greater than 0", "INVALID_AMOUNT")
  }

  const newBalance = snapshot.account.balanceNaira + input.amountNaira

  const updatedSnapshot: AppSnapshot = {
    ...snapshot,
    account: {
      ...snapshot.account,
      balanceNaira: newBalance,
    },
    transactions: [
      ...snapshot.transactions,
      {
        transactionId: generateId("txn"),
        type: "CREDIT" as const,
        amountNaira: input.amountNaira,
        description: `Fund account - ₦${input.amountNaira}`,
        createdAt: new Date().toISOString(),
      },
    ],
  }

  return {
    snapshot: updatedSnapshot,
    paymentLink: "https://payment.example.com/mock-payment-link",
    message: `Successfully funded account with ₦${input.amountNaira}. New balance: ₦${newBalance}`,
  }
}

export async function verifyImageRequest(
  snapshot: AppSnapshot,
  file: File,
): Promise<{
  snapshot: AppSnapshot
  verification: VerificationRecord
}> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 2000))

  if (!snapshot.account) {
    throw new MockApiError("No account found in session", "NO_ACCOUNT")
  }

  if (snapshot.account.balanceNaira < VERIFICATION_COST_NAIRA) {
    throw new MockApiError(
      `Insufficient balance. Required: ₦${VERIFICATION_COST_NAIRA}, Available: ₦${snapshot.account.balanceNaira}`,
      "INSUFFICIENT_BALANCE",
    )
  }

  if (!file.type.startsWith("image/")) {
    throw new MockApiError("File must be an image", "INVALID_FILE_TYPE")
  }

  // Create mock verification record
  const verification: VerificationRecord = {
    verificationId: generateId("ver"),
    imageName: file.name,
    verdict: getRandomVerdict(),
    trustScore: getRandomTrustScore(),
    billedNaira: VERIFICATION_COST_NAIRA,
    createdAt: new Date().toISOString(),
  }

  const newBalance = snapshot.account.balanceNaira - VERIFICATION_COST_NAIRA

  const updatedSnapshot: AppSnapshot = {
    ...snapshot,
    account: {
      ...snapshot.account,
      balanceNaira: newBalance,
    },
    verifications: [...snapshot.verifications, verification],
    transactions: [
      ...snapshot.transactions,
      {
        transactionId: generateId("txn"),
        type: "DEBIT" as const,
        amountNaira: VERIFICATION_COST_NAIRA,
        description: `Image verification - ${file.name}`,
        createdAt: new Date().toISOString(),
      },
    ],
    latestVerificationId: verification.verificationId,
  }

  return {
    snapshot: updatedSnapshot,
    verification,
  }
}

import type { AppSnapshot } from "@/lib/types"

export const STORAGE_KEY = "veridify_app_state"
export const VERIFICATION_COST_NAIRA = 500

export function createEmptySnapshot(): AppSnapshot {
  return {
    account: null,
    verifications: [],
    transactions: [],
    latestVerificationId: null,
  }
}

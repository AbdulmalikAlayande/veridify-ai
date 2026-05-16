import type {
  AppSnapshot,
  CreateAccountInput,
  FundAccountInput,
  FundAccountResult,
  VerifyImageResult,
} from "@/lib/types"
import {
  MockApiError,
  createMockAccount,
  fundMockAccount,
  verifyMockImage,
} from "@/lib/mock-data"
import {
  createLiveAccount,
  fundLiveAccount,
  getLiveBaseUrl,
  refreshLiveAccount,
  verifyLiveImage,
} from "@/lib/live-api"

export type ApiMode = "live" | "mock"

export function getApiMode(): ApiMode {
  return getLiveBaseUrl() ? "live" : "mock"
}

export async function createAccountRequest(
  snapshot: AppSnapshot,
  input: CreateAccountInput,
): Promise<AppSnapshot> {
  if (getApiMode() === "live") {
    return createLiveAccount(snapshot, input)
  }
  return createMockAccount(snapshot, input)
}

export async function fundAccountRequest(
  snapshot: AppSnapshot,
  input: FundAccountInput,
): Promise<FundAccountResult> {
  if (getApiMode() === "live") {
    return fundLiveAccount(snapshot, input)
  }
  return fundMockAccount(snapshot, input)
}

export async function verifyImageRequest(
  snapshot: AppSnapshot,
  file: File,
): Promise<VerifyImageResult> {
  if (getApiMode() === "live") {
    return verifyLiveImage(snapshot, file)
  }
  return verifyMockImage(snapshot, file)
}

export async function refreshAccountRequest(snapshot: AppSnapshot): Promise<AppSnapshot> {
  if (getApiMode() === "live") {
    return refreshLiveAccount(snapshot)
  }
  return snapshot
}

export { MockApiError }

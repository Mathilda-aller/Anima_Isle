import { STORAGE_KEYS } from "@/shared/constants/storage";
import type { AuthUserInfo } from "@/modules/auth/types/auth";

export function getStoredToken(): string {
  return uni.getStorageSync(STORAGE_KEYS.AUTH_TOKEN) || "";
}

export function setStoredToken(token: string): void {
  uni.setStorageSync(STORAGE_KEYS.AUTH_TOKEN, token);
}

export function clearStoredToken(): void {
  uni.removeStorageSync(STORAGE_KEYS.AUTH_TOKEN);
}

export function getStoredUser(): AuthUserInfo | null {
  const raw = uni.getStorageSync(STORAGE_KEYS.AUTH_USER);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUserInfo;
  } catch {
    return null;
  }
}

export function setStoredUser(user: AuthUserInfo): void {
  uni.setStorageSync(STORAGE_KEYS.AUTH_USER, JSON.stringify(user));
}

export function clearStoredUser(): void {
  uni.removeStorageSync(STORAGE_KEYS.AUTH_USER);
}

export function getStyleOnboardingCompleted(): boolean {
  return uni.getStorageSync(STORAGE_KEYS.STYLE_ONBOARDING_COMPLETED) === "1";
}

export function setStyleOnboardingCompleted(completed: boolean): void {
  if (completed) {
    uni.setStorageSync(STORAGE_KEYS.STYLE_ONBOARDING_COMPLETED, "1");
    return;
  }
  uni.removeStorageSync(STORAGE_KEYS.STYLE_ONBOARDING_COMPLETED);
}

export function clearAuthStorage(): void {
  clearStoredToken();
  clearStoredUser();
}

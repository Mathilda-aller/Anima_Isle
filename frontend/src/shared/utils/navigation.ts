import { ROUTES } from "@/shared/constants/routes";

let navigationLocked = false;
let navigationReleaseTimer: ReturnType<typeof setTimeout> | null = null;

function lockNavigation(duration = 420): boolean {
  if (navigationLocked) {
    return false;
  }

  navigationLocked = true;
  if (navigationReleaseTimer) {
    clearTimeout(navigationReleaseTimer);
  }
  navigationReleaseTimer = setTimeout(() => {
    navigationLocked = false;
    navigationReleaseTimer = null;
  }, duration);
  return true;
}

function pulseTapFeedback(): void {
  try {
    uni.vibrateShort?.({
      type: "light",
    } as never);
  } catch {
    // Ignore devices that do not support haptics.
  }
}

export function navigateToWithFeedback(url: string): void {
  if (!lockNavigation()) {
    return;
  }

  pulseTapFeedback();
  uni.navigateTo({ url });
}

export function reLaunchWithFeedback(url: string): void {
  if (!lockNavigation()) {
    return;
  }

  pulseTapFeedback();
  uni.reLaunch({ url });
}

export function toLogin(): void {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1];
  if (current?.route === ROUTES.AUTH_LOGIN.replace(/^\//, "")) {
    return;
  }
  reLaunchWithFeedback(ROUTES.AUTH_LOGIN);
}

export function toChatHome(): void {
  reLaunchWithFeedback(ROUTES.CHAT_HOME);
}

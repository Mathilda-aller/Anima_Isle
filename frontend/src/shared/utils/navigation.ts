import { ROUTES } from "@/shared/constants/routes";

export function toLogin(): void {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1];
  if (current?.route === ROUTES.AUTH_LOGIN.replace(/^\//, "")) {
    return;
  }
  uni.reLaunch({ url: ROUTES.AUTH_LOGIN });
}

export function toChatHome(): void {
  uni.reLaunch({ url: ROUTES.CHAT_HOME });
}

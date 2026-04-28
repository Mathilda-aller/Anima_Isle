import { STORAGE_KEYS } from "@/shared/constants/storage";

export interface ChatDraft {
  sessionId: string;
  step: number;
  answer1: string;
}

export function getChatDraft(): ChatDraft | null {
  const raw = uni.getStorageSync(STORAGE_KEYS.CHAT_DRAFT);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as ChatDraft;
  } catch {
    return null;
  }
}

export function setChatDraft(draft: ChatDraft): void {
  uni.setStorageSync(STORAGE_KEYS.CHAT_DRAFT, JSON.stringify(draft));
}

export function clearChatDraft(): void {
  uni.removeStorageSync(STORAGE_KEYS.CHAT_DRAFT);
}

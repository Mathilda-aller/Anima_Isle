import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

vi.mock("@/modules/chat/api/chat", () => ({
  startChat: vi.fn(),
  replyChat: vi.fn(),
  replyChatCancelable: vi.fn(),
  confirmTicket: vi.fn(),
  replyChatStreamCancelable: vi.fn(),
}));

vi.mock("@/infrastructure/storage/chat", () => ({
  clearChatDraft: vi.fn(),
  setChatDraft: vi.fn(),
}));

vi.mock("@/infrastructure/http/tracking", () => ({
  logEvent: vi.fn().mockResolvedValue(undefined),
}));

import { replyChatCancelable, replyChatStreamCancelable } from "@/modules/chat/api/chat";
import { useChatStore } from "@/modules/chat/store/chat";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("chat store request isolation", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("ignores late first-answer replies after the session is reset", async () => {
    const store = useChatStore();
    const pending = deferred<{ session_id: string; state: "processing"; reply_text: string }>();
    const cancel = vi.fn();

    vi.mocked(replyChatCancelable).mockReturnValue({
      promise: pending.promise as Promise<any>,
      cancel,
    });

    store.sessionId = "session-a";
    store.step = 0;

    const submitPromise = store.submitAnswer("第一轮");
    store.resetSession();
    pending.resolve({
      session_id: "session-a",
      state: "processing",
      reply_text: "旧的第二问",
    });
    await submitPromise;

    expect(cancel).toHaveBeenCalledTimes(1);
    expect(store.step).toBe(0);
    expect(store.q2).toBe("");
  });

  it("drops stale stream events after a reset", async () => {
    const store = useChatStore();
    const pending = deferred<void>();
    const cancel = vi.fn();
    let onEvent: ((event: { event: string; data: Record<string, unknown> }) => void) | undefined;

    vi.mocked(replyChatStreamCancelable).mockImplementation((_payload, options) => {
      onEvent = options.onEvent as typeof onEvent;
      return {
        promise: pending.promise,
        cancel,
      };
    });

    store.sessionId = "session-b";
    store.step = 1;
    store.pendingFinalAnswer = "第二轮";

    const streamPromise = store.streamPendingFinalAnswer();
    store.resetSession();

    onEvent?.({
      event: "asset_ready",
      data: {
        ticket_data: {
          ticket_uid: "ticket-old",
          image_url: "https://img/old.jpg",
          poem_content: "old",
          candidate_images: [],
        },
      },
    });
    pending.resolve();
    await streamPromise;

    expect(cancel).toHaveBeenCalledTimes(1);
    expect(store.ticketDraft).toBeNull();
    expect(store.step).toBe(0);
  });
});

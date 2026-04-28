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

import { confirmTicket, replyChatCancelable, replyChatStreamCancelable } from "@/modules/chat/api/chat";
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

  it("switches poem content when choosing another candidate", () => {
    const store = useChatStore();
    store.ticketDraft = {
      id: 1,
      ticket_uid: "ticket-1",
      image_url: "https://img/old.jpg",
      poem_content: "旧诗句",
      island_category: "RAIN",
      is_public: false,
      created_at: "2026-04-21T00:00:00",
      recommended_tags: ["#a", "#b", "#c", "#d", "#e"],
      candidate_images: [
        { image_url: "https://img/old.jpg", poem_content: "旧诗句" },
        { image_url: "https://img/new.jpg", poem_content: "新诗句" },
      ],
    };

    store.chooseCandidate("https://img/new.jpg");

    expect(store.ticketDraft?.image_url).toBe("https://img/new.jpg");
    expect(store.ticketDraft?.poem_content).toBe("新诗句");
    expect(store.rerollCount).toBe(1);
  });

  it("cycles candidate selection across multiple rerolls", () => {
    const store = useChatStore();
    store.ticketDraft = {
      id: 1,
      ticket_uid: "ticket-2",
      image_url: "https://img/a.jpg",
      poem_content: "诗句-A",
      island_category: "RAIN",
      is_public: false,
      created_at: "2026-04-21T00:00:00",
      recommended_tags: ["#a", "#b", "#c", "#d", "#e"],
      candidate_images: [
        { image_url: "https://img/a.jpg", poem_content: "诗句-A" },
        { image_url: "https://img/b.jpg", poem_content: "诗句-B" },
        { image_url: "https://img/c.jpg", poem_content: "诗句-C" },
      ],
    };

    store.chooseCandidate("https://img/b.jpg");
    expect(store.ticketDraft?.image_url).toBe("https://img/b.jpg");
    expect(store.ticketDraft?.poem_content).toBe("诗句-B");

    store.chooseCandidate("https://img/c.jpg");
    expect(store.ticketDraft?.image_url).toBe("https://img/c.jpg");
    expect(store.ticketDraft?.poem_content).toBe("诗句-C");

    store.chooseCandidate("https://img/a.jpg");
    expect(store.ticketDraft?.image_url).toBe("https://img/a.jpg");
    expect(store.ticketDraft?.poem_content).toBe("诗句-A");
    expect(store.rerollCount).toBe(3);
  });

  it("keeps the first matching poem when duplicate image urls are provided", () => {
    const store = useChatStore();
    store.ticketDraft = {
      id: 1,
      ticket_uid: "ticket-3",
      image_url: "https://img/a.jpg",
      poem_content: "诗句-A",
      island_category: "RAIN",
      is_public: false,
      created_at: "2026-04-21T00:00:00",
      recommended_tags: ["#a", "#b", "#c", "#d", "#e"],
      candidate_images: [
        { image_url: "https://img/a.jpg", poem_content: "诗句-A" },
        { image_url: "https://img/a.jpg", poem_content: "诗句-A-重复" },
      ],
    };

    store.chooseCandidate("https://img/a.jpg");

    expect(store.ticketDraft?.image_url).toBe("https://img/a.jpg");
    expect(store.ticketDraft?.poem_content).toBe("诗句-A");
  });

  it("submits the current poem when confirming a ticket", async () => {
    const store = useChatStore();
    vi.mocked(confirmTicket).mockResolvedValue({
      ticket_uid: "ticket-1",
      final_image_url: "https://img/new.jpg",
      reroll_count: 1,
    } as any);

    store.sessionId = "session-c";
    store.rerollCount = 1;
    store.ticketDraft = {
      id: 1,
      ticket_uid: "ticket-1",
      image_url: "https://img/new.jpg",
      poem_content: "当前诗句",
      island_category: "RAIN",
      is_public: false,
      created_at: "2026-04-21T00:00:00",
      recommended_tags: ["#a", "#b", "#c", "#d", "#e"],
      candidate_images: [{ image_url: "https://img/new.jpg", poem_content: "当前诗句" }],
    };

    await store.confirmTicketSelection();

    expect(confirmTicket).toHaveBeenCalledWith({
      ticket_uid: "ticket-1",
      final_image_url: "https://img/new.jpg",
      final_poem_content: "当前诗句",
      reroll_count: 1,
    });
  });
});

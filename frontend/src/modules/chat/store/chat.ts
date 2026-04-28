import { defineStore } from "pinia";
import { startChat, confirmTicket, replyChatStreamCancelable } from "@/modules/chat/api/chat";
import { isRequestAbortedError } from "@/infrastructure/http/request";
import type { ChatSessionState, ChatStreamEvent } from "@/modules/chat/types/chat";
import { clearChatDraft, setChatDraft } from "@/infrastructure/storage/chat";
import { logEvent } from "@/infrastructure/http/tracking";

type ChatRequestKind = "voice_transcribe" | "reply_stream";

interface ActiveRequestEntry {
  token: number;
  sessionId: string;
  cancel: (() => void) | null;
}

const requestCounters: Record<ChatRequestKind, number> = {
  voice_transcribe: 0,
  reply_stream: 0,
};

const activeRequests: Record<ChatRequestKind, ActiveRequestEntry> = {
  voice_transcribe: { token: 0, sessionId: "", cancel: null },
  reply_stream: { token: 0, sessionId: "", cancel: null },
};

export const useChatStore = defineStore("chat", {
  state: (): ChatSessionState => ({
    sessionId: "",
    step: 0,
    q1: "",
    answer1: "",
    pendingAnswer: "",
    pendingAnswerIsVoice: false,
    pendingAnswerDuration: 0,
    generationState: "idle",
    replyText: "",
    ticketDraft: null,
    rerollCount: 0,
    loading: false,
    streamError: "",
  }),
  actions: {
    beginTrackedRequest(kind: ChatRequestKind, sessionId: string, cancel?: () => void) {
      const previousCancel = activeRequests[kind].cancel;
      if (previousCancel) {
        previousCancel();
      }

      requestCounters[kind] += 1;
      const token = requestCounters[kind];
      activeRequests[kind] = {
        token,
        sessionId,
        cancel: cancel ?? null,
      };
      return { token, sessionId };
    },

    attachTrackedRequestCancel(kind: ChatRequestKind, token: number, sessionId: string, cancel: () => void) {
      if (!this.isTrackedRequestCurrent(kind, token, sessionId)) {
        cancel();
        return;
      }

      const previousCancel = activeRequests[kind].cancel;
      if (previousCancel && previousCancel !== cancel) {
        previousCancel();
      }
      activeRequests[kind].cancel = cancel;
    },

    isTrackedRequestCurrent(kind: ChatRequestKind, token: number, sessionId: string) {
      const current = activeRequests[kind];
      return current.token === token && current.sessionId === sessionId;
    },

    finishTrackedRequest(kind: ChatRequestKind, token: number, sessionId: string) {
      if (!this.isTrackedRequestCurrent(kind, token, sessionId)) {
        return false;
      }

      activeRequests[kind].cancel = null;
      activeRequests[kind].sessionId = "";
      return true;
    },

    cancelActiveChatWork(kinds: ChatRequestKind[] = ["voice_transcribe", "reply_stream"]) {
      kinds.forEach((kind) => {
        const cancel = activeRequests[kind].cancel;
        requestCounters[kind] += 1;
        activeRequests[kind] = {
          token: requestCounters[kind],
          sessionId: "",
          cancel: null,
        };
        cancel?.();
      });
      this.loading = false;
    },

    resetSession() {
      this.cancelActiveChatWork();
      this.sessionId = "";
      this.step = 0;
      this.q1 = "";
      this.answer1 = "";
      this.pendingAnswer = "";
      this.pendingAnswerIsVoice = false;
      this.pendingAnswerDuration = 0;
      this.generationState = "idle";
      this.replyText = "";
      this.ticketDraft = null;
      this.rerollCount = 0;
      this.streamError = "";
      clearChatDraft();
    },

    async startSession() {
      this.loading = true;
      try {
        const res = await startChat();
        this.sessionId = res.session_id;
        this.q1 = res.first_question;
        this.step = 0;
        this.answer1 = "";
        this.pendingAnswer = "";
        this.pendingAnswerIsVoice = false;
        this.pendingAnswerDuration = 0;
        this.generationState = "idle";
        this.replyText = "";
        this.ticketDraft = null;
        this.rerollCount = 0;
        this.streamError = "";
        await logEvent("chat_session_started", { session_id: this.sessionId });
      } finally {
        this.loading = false;
      }
    },

    queuePendingAnswer(
      content: string,
      options: {
        isVoice?: boolean;
        duration?: number;
      } = {},
    ) {
      const clean = content.trim();
      if (!clean || !this.sessionId || this.step >= 2) return;

      this.answer1 = clean;
      this.pendingAnswer = clean;
      this.pendingAnswerIsVoice = options.isVoice ?? false;
      this.pendingAnswerDuration = options.duration ?? 0;
      this.step = 1;
      this.generationState = "processing";
      this.replyText = "";
      this.ticketDraft = null;
      this.rerollCount = 0;
      this.streamError = "";

      setChatDraft({
        sessionId: this.sessionId,
        step: this.step,
        answer1: this.answer1,
      });
    },

    applyStreamEvent(event: ChatStreamEvent) {
      if (event.event === "ack") {
        this.step = 1;
        this.generationState = "processing";
        this.streamError = "";
        return;
      }

      if (event.event === "risk") {
        const level = String((event.data as Record<string, unknown>).level || "SAFE");
        if (level === "DANGER") {
          this.step = 2;
          this.generationState = "risk_blocked";
        }
        return;
      }

      if (event.event === "empathy_delta") {
        const delta = String((event.data as Record<string, unknown>).delta || "");
        this.generationState = "reply_streaming";
        this.replyText += delta;
        return;
      }

      if (event.event === "empathy_done") {
        const replyText = String((event.data as Record<string, unknown>).reply_text || this.replyText);
        this.replyText = replyText;
        this.generationState = "asset_loading";
        return;
      }

      if (event.event === "asset_started") {
        if (this.generationState !== "reply_streaming") {
          this.generationState = "asset_loading";
        }
        return;
      }

      if (event.event === "asset_ready") {
        const ticketData = (event.data as Record<string, unknown>).ticket_data;
        this.ticketDraft = ticketData as ChatSessionState["ticketDraft"];
        this.step = 3;
        this.generationState = "finished";
        return;
      }

      if (event.event === "error") {
        this.streamError = String((event.data as Record<string, unknown>).message || "生成失败，请稍后再试");
        this.generationState = "error";
        return;
      }
    },

    async streamPendingAnswer() {
      if (!this.pendingAnswer || !this.sessionId) return;

      const sessionId = this.sessionId;
      const content = this.pendingAnswer;
      const isVoice = this.pendingAnswerIsVoice;
      const duration = this.pendingAnswerDuration;
      const requestMeta = this.beginTrackedRequest("reply_stream", sessionId);

      this.pendingAnswer = "";
      this.pendingAnswerIsVoice = false;
      this.pendingAnswerDuration = 0;
      this.loading = true;
      this.replyText = "";
      this.ticketDraft = null;
      this.streamError = "";
      this.generationState = "processing";
      this.step = 1;

      try {
        const operation = replyChatStreamCancelable(
          {
            session_id: this.sessionId,
            content,
            is_voice: isVoice,
            duration,
          },
          {
            onEvent: (event) => {
              if (!this.isTrackedRequestCurrent("reply_stream", requestMeta.token, sessionId)) {
                return;
              }
              this.applyStreamEvent(event);
            },
          },
        );
        this.attachTrackedRequestCancel("reply_stream", requestMeta.token, sessionId, operation.cancel);
        await operation.promise;

        if (!this.isTrackedRequestCurrent("reply_stream", requestMeta.token, sessionId)) {
          return;
        }

        await logEvent("chat_reply_streamed", {
          session_id: this.sessionId,
          state: this.generationState,
        });
      } catch (error) {
        if (isRequestAbortedError(error) || !this.isTrackedRequestCurrent("reply_stream", requestMeta.token, sessionId)) {
          return;
        }
        throw error;
      } finally {
        if (this.finishTrackedRequest("reply_stream", requestMeta.token, sessionId)) {
          this.loading = false;
        }
      }
    },

    chooseCandidate(imageUrl: string) {
      if (!this.ticketDraft) return;
      const matched = this.ticketDraft.candidate_images.find((item) => item.image_url === imageUrl);
      this.ticketDraft = {
        ...this.ticketDraft,
        image_url: imageUrl,
        poem_content: matched?.poem_content || this.ticketDraft.poem_content,
      };
      this.rerollCount += 1;
    },

    async confirmTicketSelection() {
      if (!this.ticketDraft) return;

      await confirmTicket({
        ticket_uid: this.ticketDraft.ticket_uid,
        final_image_url: this.ticketDraft.image_url,
        final_poem_content: this.ticketDraft.poem_content,
        reroll_count: this.rerollCount,
      });

      await logEvent("chat_ticket_confirmed", {
        session_id: this.sessionId,
        ticket_uid: this.ticketDraft.ticket_uid,
        reroll_count: this.rerollCount,
      });
      clearChatDraft();
    },
  },
});

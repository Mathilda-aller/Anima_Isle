import { buildUrl, isRequestAbortedError, request, requestCancelable, type CancelableRequest } from "@/infrastructure/http/request";
import { getStoredToken } from "@/infrastructure/storage/auth";
import { ApiError } from "@/shared/types/http";
import type {
  ChatStreamEvent,
  ChatReplyRequest,
  ChatStartResponse,
  ChatStepResponse,
  ChatVoiceTranscribeResponse,
  TicketConfirmRequest,
} from "@/modules/chat/types/chat";

interface TicketConfirmResponse {
  ticket_uid: string;
  final_image_url: string;
  reroll_count: number;
}

export interface CancelableStreamRequest {
  promise: Promise<void>;
  cancel: () => void;
}

export function startChat() {
  return request<ChatStartResponse>({
    path: "/chat/start",
    method: "POST",
    data: {},
  });
}

export function replyChat(payload: ChatReplyRequest) {
  return request<ChatStepResponse, ChatReplyRequest>({
    path: "/chat/reply",
    method: "POST",
    data: payload,
  });
}

export function replyChatCancelable(payload: ChatReplyRequest): CancelableRequest<ChatStepResponse> {
  return requestCancelable<ChatStepResponse, ChatReplyRequest>({
    path: "/chat/reply",
    method: "POST",
    data: payload,
  });
}

interface ReplyChatStreamOptions {
  onEvent: (event: ChatStreamEvent) => void;
}

interface ChunkDecoder {
  decode: (chunk?: ArrayBuffer, stream?: boolean) => string;
}

function parseSseChunk(rawChunk: string, onEvent: (event: ChatStreamEvent) => void) {
  const blocks = rawChunk.split("\n\n");
  const completeBlocks = rawChunk.endsWith("\n\n") ? blocks : blocks.slice(0, -1);
  const remainder = rawChunk.endsWith("\n\n") ? "" : blocks[blocks.length - 1] || "";

  completeBlocks.forEach((block) => {
    const lines = block.split("\n");
    let eventName = "message";
    const dataLines: string[] = [];

    lines.forEach((line) => {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    });

    if (!dataLines.length) return;
    const payload = dataLines.join("\n");
    try {
      onEvent({
        event: eventName as ChatStreamEvent["event"],
        data: JSON.parse(payload),
      });
    } catch {
      onEvent({
        event: eventName as ChatStreamEvent["event"],
        data: { raw: payload },
      });
    }
  });

  return remainder;
}

function createChunkDecoder(): ChunkDecoder {
  if (typeof TextDecoder !== "undefined") {
    const decoder = new TextDecoder("utf-8");
    return {
      decode: (chunk?: ArrayBuffer, stream = true) => decoder.decode(chunk ? new Uint8Array(chunk) : undefined, { stream }),
    };
  }

  return {
    decode: (chunk?: ArrayBuffer) => {
      if (!chunk) return "";
      const bytes = new Uint8Array(chunk);
      let text = "";
      for (let index = 0; index < bytes.length; index += 1) {
        text += String.fromCharCode(bytes[index]);
      }
      try {
        return decodeURIComponent(escape(text));
      } catch {
        return text;
      }
    },
  };
}

function toArrayBuffer(data: unknown): ArrayBuffer | null {
  if (data instanceof ArrayBuffer) return data;
  if (typeof ArrayBuffer !== "undefined" && ArrayBuffer.isView(data)) {
    const view = data as ArrayBufferView;
    return view.buffer.slice(view.byteOffset, view.byteOffset + view.byteLength);
  }
  return null;
}

async function replyChatStreamViaFetch(payload: ChatReplyRequest, options: ReplyChatStreamOptions, signal?: AbortSignal) {
  const token = getStoredToken();
  let response: Response;
  try {
    response = await fetch(buildUrl("/chat/reply/stream"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (error) {
    if ((error as Error | undefined)?.name === "AbortError") {
      throw new ApiError({ statusCode: 0, detail: "request_aborted" });
    }
    throw error;
  }

  if (!response.ok) {
    let detail: string | Record<string, unknown> = "request_failed";
    try {
      const errorPayload = await response.json();
      if (typeof errorPayload?.detail === "string") detail = errorPayload.detail;
      else if (errorPayload?.detail) detail = errorPayload.detail;
    } catch {
      detail = response.statusText || "request_failed";
    }
    throw new ApiError({ statusCode: response.status, detail });
  }

  if (!response.body) {
    throw new ApiError({ statusCode: 0, detail: "stream_not_supported" });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    buffer = parseSseChunk(buffer, options.onEvent) || "";
  }

  if (buffer.trim()) {
    parseSseChunk(`${buffer}\n\n`, options.onEvent);
  }
}

async function replyChatStreamViaUniRequest(
  payload: ChatReplyRequest,
  options: ReplyChatStreamOptions,
  onTaskCreated?: (task: { abort?: () => void }) => void,
) {
  const token = getStoredToken();
  const decoder = createChunkDecoder();
  let buffer = "";
  let cancelled = false;

  await new Promise<void>((resolve, reject) => {
    const requestTask = uni.request({
      url: buildUrl("/chat/reply/stream"),
      method: "POST",
      timeout: 60000,
      enableChunked: true,
      responseType: "arraybuffer",
      dataType: "text",
      data: payload,
      header: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(normalizeStreamRequestError(res.statusCode, res.data));
          return;
        }

        const tail = decoder.decode(undefined, false);
        if (tail) {
          buffer += tail;
        }
        if (buffer.trim()) {
          parseSseChunk(`${buffer}\n\n`, options.onEvent);
        }
        resolve();
      },
      fail: (err) => {
        reject(
          cancelled
            ? new ApiError({ statusCode: 0, detail: "request_aborted" })
            : new ApiError({
                statusCode: 0,
                detail: err.errMsg || "network_error",
              }),
        );
      },
    });

    const chunkedRequestTask = requestTask as unknown as {
      onChunkReceived?: (callback: (result: { data: ArrayBuffer }) => void) => void;
    };

    if (typeof chunkedRequestTask.onChunkReceived !== "function") {
      requestTask.abort();
      reject(new ApiError({ statusCode: 0, detail: "stream_not_supported" }));
      return;
    }

    chunkedRequestTask.onChunkReceived((result) => {
      const chunk = toArrayBuffer(result.data);
      if (!chunk) return;
      buffer += decoder.decode(chunk, true);
      buffer = parseSseChunk(buffer, options.onEvent) || "";
    });

    onTaskCreated?.({
      abort: () => {
        cancelled = true;
        requestTask.abort();
      },
    });
  });
}

function normalizeStreamRequestError(statusCode: number, payload: unknown): ApiError {
  let detail: string | Record<string, unknown> = "request_failed";

  if (typeof payload === "string" && payload.trim()) {
    detail = payload;
  } else if (payload instanceof ArrayBuffer) {
    const text = createChunkDecoder().decode(payload, false).trim();
    if (text) {
      try {
        const parsed = JSON.parse(text) as { detail?: string | Record<string, unknown> };
        detail = parsed.detail || text;
      } catch {
        detail = text;
      }
    }
  } else if (typeof payload === "object" && payload !== null && "detail" in payload) {
    detail = (payload as { detail: string | Record<string, unknown> }).detail;
  }

  return new ApiError({ statusCode, detail });
}

async function replyChatStreamFallback(payload: ChatReplyRequest, options: ReplyChatStreamOptions) {
  options.onEvent({ event: "ack", data: { session_id: payload.session_id } });
  const result = await replyChat(payload);

  if (result.state === "risk_blocked") {
    options.onEvent({
      event: "risk",
      data: { level: "DANGER", reason_code: "compat_sync", should_block: true, hit_type: "compat_sync" },
    });
    options.onEvent({ event: "done", data: { status: "risk_blocked" } });
    return;
  }

  options.onEvent({
    event: "risk",
    data: { level: "SAFE", reason_code: "compat_sync", should_block: false, hit_type: "compat_sync" },
  });
  options.onEvent({ event: "asset_started", data: {} });
  options.onEvent({ event: "empathy_done", data: { reply_text: result.reply_text } });
  if (result.ticket_data) {
    options.onEvent({ event: "asset_ready", data: { ticket_data: result.ticket_data } });
  }
  options.onEvent({ event: "done", data: { status: result.state } });
}

function shouldFallbackToSyncCompat(): boolean {
  // #ifndef H5
  // #ifndef MP-WEIXIN
  return true;
  // #endif
  // #endif

  return false;
}

export async function replyChatStream(payload: ChatReplyRequest, options: ReplyChatStreamOptions) {
  return replyChatStreamCancelable(payload, options).promise;
}

export function replyChatStreamCancelable(payload: ChatReplyRequest, options: ReplyChatStreamOptions): CancelableStreamRequest {
  const fetchController = typeof AbortController !== "undefined" ? new AbortController() : null;
  let cancel = () => {
    fetchController?.abort();
  };

  const promise = (async () => {
    try {
      // #ifdef H5
      const supportsStreaming =
        typeof fetch === "function" &&
        typeof TextDecoder !== "undefined" &&
        typeof ReadableStream !== "undefined";

      if (!supportsStreaming) {
        throw new ApiError({ statusCode: 0, detail: "stream_not_supported_on_h5" });
      }

      await replyChatStreamViaFetch(payload, options, fetchController?.signal);
      return;
      // #endif

      // #ifdef MP-WEIXIN
      await replyChatStreamViaUniRequest(payload, options, (task) => {
        cancel = () => {
          task.abort?.();
        };
      });
      return;
      // #endif

      await replyChatStreamFallback(payload, options);
    } catch (error) {
      if (isRequestAbortedError(error)) {
        throw error;
      }

      if (
        error instanceof ApiError &&
        typeof error.detail === "string" &&
        error.detail === "stream_not_supported" &&
        shouldFallbackToSyncCompat()
      ) {
        await replyChatStreamFallback(payload, options);
        return;
      }
      throw error;
    }
  })();

  return {
    promise,
    cancel: () => {
      cancel();
    },
  };
}

export function transcribeVoice(payload: FormData) {
  return request<ChatVoiceTranscribeResponse, FormData>({
    path: "/chat/transcribe",
    method: "POST",
    data: payload,
  });
}

export function transcribeVoiceCancelable(payload: FormData): CancelableRequest<ChatVoiceTranscribeResponse> {
  return requestCancelable<ChatVoiceTranscribeResponse, FormData>({
    path: "/chat/transcribe",
    method: "POST",
    data: payload,
  });
}

export function confirmTicket(payload: TicketConfirmRequest) {
  return request<TicketConfirmResponse, TicketConfirmRequest>({
    path: "/chat/confirm",
    method: "POST",
    data: payload,
  });
}

export const CHAT_API_INTERNALS = {
  replyChatStreamViaFetch,
  replyChatStreamViaUniRequest,
};

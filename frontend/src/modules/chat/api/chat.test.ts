import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CHAT_API_INTERNALS, replyChatStreamCancelable, transcribeVoiceCancelable } from "@/modules/chat/api/chat";
import { ApiError } from "@/shared/types/http";

describe("chat api cancellation", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.stubGlobal("uni", {
      request: vi.fn(),
      getStorageSync: vi.fn(() => ""),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("aborts the H5 streaming request when cancelled", async () => {
    const fetchMock = vi.fn((_url: string, init?: RequestInit) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => {
        const error = new Error("aborted");
        error.name = "AbortError";
        reject(error);
      });
    }));
    vi.stubGlobal("fetch", fetchMock);

    const operation = replyChatStreamCancelable(
      { session_id: "session-1", content: "第二轮" },
      { onEvent: vi.fn() },
    );

    operation.cancel();

    await expect(operation.promise).rejects.toMatchObject({ detail: "request_aborted" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("wires the mini-program stream abort handle to requestTask.abort", async () => {
    const abort = vi.fn();
    const onChunkReceived = vi.fn();
    const requestTask = { abort, onChunkReceived };
    let requestOptions: { fail?: (error: { errMsg: string }) => void } | null = null;
    const requestMock = vi.fn((options: { fail?: (error: { errMsg: string }) => void }) => {
      requestOptions = options;
      return requestTask;
    });
    vi.stubGlobal("uni", { request: requestMock, getStorageSync: vi.fn(() => "") });

    let cancel: (() => void) | undefined;
    const streamPromise = CHAT_API_INTERNALS.replyChatStreamViaUniRequest(
      { session_id: "session-2", content: "第二轮" },
      { onEvent: vi.fn() },
      (task) => {
        cancel = () => {
          task.abort?.();
        };
      },
    );

    cancel?.();
    const streamFail = (requestOptions as { fail?: (error: { errMsg: string }) => void } | null)?.fail;
    streamFail?.({ errMsg: "request:fail abort" });

    await expect(streamPromise).rejects.toMatchObject({ detail: "request_aborted" });
    expect(abort).toHaveBeenCalledTimes(1);
  });

  it("aborts transcribe requests through the generic request task", async () => {
    const abort = vi.fn();
    let requestOptions: { fail?: (error: { errMsg: string }) => void } | null = null;
    const requestMock = vi.fn((options: { fail?: (error: { errMsg: string }) => void }) => {
      requestOptions = options;
      return { abort };
    });
    vi.stubGlobal("uni", { request: requestMock, getStorageSync: vi.fn(() => "") });

    const operation = transcribeVoiceCancelable(new FormData());
    operation.cancel();

    const requestFail = (requestOptions as { fail?: (error: { errMsg: string }) => void } | null)?.fail;
    requestFail?.({ errMsg: "request:fail abort" });

    await expect(operation.promise).rejects.toMatchObject({ detail: "request_aborted" });
    expect(abort).toHaveBeenCalledTimes(1);
  });
});

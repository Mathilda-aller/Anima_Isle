import { describe, expect, it, vi } from "vitest";

import {
  COMFORT_STAGE_LONG_DELAY_MS,
  COMFORT_STAGE_MEDIUM_DELAY_MS,
  COMFORT_STAGE_SHORT_DELAY_MS,
  IMAGE_PRELOAD_TIMEOUT_MS,
  TRANSITION_STAGE_MIN_DELAY_MS,
  getComfortStageDelayMs,
  runRevealStageSequence,
} from "@/modules/chat/utils/generatingFlow";

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function waitForDelay(delay: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, delay);
  });
}

describe("generatingFlow", () => {
  it("uses the tuned comfort delay defaults", () => {
    expect(COMFORT_STAGE_SHORT_DELAY_MS).toBe(2500);
    expect(COMFORT_STAGE_MEDIUM_DELAY_MS).toBe(3500);
    expect(COMFORT_STAGE_LONG_DELAY_MS).toBe(4500);
    expect(IMAGE_PRELOAD_TIMEOUT_MS).toBe(20000);
  });

  it("maps comfort copy length to the expected minimum delay", () => {
    expect(getComfortStageDelayMs("短句")).toBe(COMFORT_STAGE_SHORT_DELAY_MS);
    expect(getComfortStageDelayMs("a".repeat(60))).toBe(COMFORT_STAGE_MEDIUM_DELAY_MS);
    expect(getComfortStageDelayMs("a".repeat(100))).toBe(COMFORT_STAGE_LONG_DELAY_MS);
  });

  it("keeps the reply stage until the comfort delay is reached", async () => {
    vi.useFakeTimers();
    const onTransitionStart = vi.fn();
    const onRevealReady = vi.fn();
    const onImageFailed = vi.fn();

    const sequence = runRevealStageSequence({
      comfortDelayMs: COMFORT_STAGE_SHORT_DELAY_MS,
      transitionDelayMs: TRANSITION_STAGE_MIN_DELAY_MS,
      imageReadyPromise: Promise.resolve(true),
      waitForDelay,
      isCurrent: () => true,
      onTransitionStart,
      onRevealReady,
      onImageFailed,
    });

    await vi.advanceTimersByTimeAsync(COMFORT_STAGE_SHORT_DELAY_MS - 1);
    expect(onTransitionStart).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);
    expect(onTransitionStart).toHaveBeenCalledTimes(1);
    expect(onRevealReady).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(TRANSITION_STAGE_MIN_DELAY_MS);
    await sequence;
    expect(onRevealReady).toHaveBeenCalledTimes(1);
    expect(onImageFailed).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it("waits in the transition stage until the image is ready", async () => {
    vi.useFakeTimers();
    const onTransitionStart = vi.fn();
    const onRevealReady = vi.fn();
    const deferred = createDeferred<boolean>();

    const sequence = runRevealStageSequence({
      comfortDelayMs: COMFORT_STAGE_SHORT_DELAY_MS,
      transitionDelayMs: TRANSITION_STAGE_MIN_DELAY_MS,
      imageReadyPromise: deferred.promise,
      waitForDelay,
      isCurrent: () => true,
      onTransitionStart,
      onRevealReady,
      onImageFailed: vi.fn(),
    });

    await vi.advanceTimersByTimeAsync(COMFORT_STAGE_SHORT_DELAY_MS + TRANSITION_STAGE_MIN_DELAY_MS);
    expect(onTransitionStart).toHaveBeenCalledTimes(1);
    expect(onRevealReady).not.toHaveBeenCalled();

    deferred.resolve(true);
    await Promise.resolve();
    await sequence;
    expect(onRevealReady).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it("keeps the transition stage and reports an error when the image fails", async () => {
    vi.useFakeTimers();
    const onTransitionStart = vi.fn();
    const onImageFailed = vi.fn();

    const sequence = runRevealStageSequence({
      comfortDelayMs: COMFORT_STAGE_SHORT_DELAY_MS,
      transitionDelayMs: TRANSITION_STAGE_MIN_DELAY_MS,
      imageReadyPromise: Promise.resolve(false),
      waitForDelay,
      isCurrent: () => true,
      onTransitionStart,
      onRevealReady: vi.fn(),
      onImageFailed,
    });

    await vi.advanceTimersByTimeAsync(COMFORT_STAGE_SHORT_DELAY_MS + TRANSITION_STAGE_MIN_DELAY_MS);
    await sequence;
    expect(onTransitionStart).toHaveBeenCalledTimes(1);
    expect(onImageFailed).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});

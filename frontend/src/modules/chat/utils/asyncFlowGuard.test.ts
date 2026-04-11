import { describe, expect, it, vi } from "vitest";

import { createAsyncFlowGuard } from "@/modules/chat/utils/asyncFlowGuard";

describe("createAsyncFlowGuard", () => {
  it("runs scheduled callbacks for the current token only", () => {
    vi.useFakeTimers();
    const guard = createAsyncFlowGuard();
    const callback = vi.fn();

    const token = guard.begin();
    guard.schedule(token, callback, 50);
    vi.advanceTimersByTime(50);

    expect(callback).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it("drops scheduled callbacks after invalidation", () => {
    vi.useFakeTimers();
    const guard = createAsyncFlowGuard();
    const callback = vi.fn();

    const token = guard.begin();
    guard.schedule(token, callback, 50);
    guard.invalidate();
    vi.advanceTimersByTime(50);

    expect(callback).not.toHaveBeenCalled();
    vi.useRealTimers();
  });
});

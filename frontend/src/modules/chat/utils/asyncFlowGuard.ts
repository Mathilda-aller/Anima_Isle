export interface AsyncFlowGuard {
  begin: () => number;
  invalidate: () => void;
  isCurrent: (token: number) => boolean;
  schedule: (token: number, callback: () => void, delay: number) => ReturnType<typeof setTimeout>;
}

export function createAsyncFlowGuard(): AsyncFlowGuard {
  let currentToken = 0;
  const timers = new Set<ReturnType<typeof setTimeout>>();

  const clearTimers = () => {
    timers.forEach((timer) => clearTimeout(timer));
    timers.clear();
  };

  return {
    begin() {
      currentToken += 1;
      clearTimers();
      return currentToken;
    },
    invalidate() {
      currentToken += 1;
      clearTimers();
    },
    isCurrent(token: number) {
      return token === currentToken;
    },
    schedule(token: number, callback: () => void, delay: number) {
      const timer = setTimeout(() => {
        timers.delete(timer);
        if (!this.isCurrent(token)) {
          return;
        }
        callback();
      }, delay);
      timers.add(timer);
      return timer;
    },
  };
}

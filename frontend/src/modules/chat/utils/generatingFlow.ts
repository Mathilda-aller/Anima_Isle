export const COMFORT_STAGE_SHORT_MAX_LENGTH = 40;
export const COMFORT_STAGE_MEDIUM_MAX_LENGTH = 80;
export const COMFORT_STAGE_SHORT_DELAY_MS = 2500;
export const COMFORT_STAGE_MEDIUM_DELAY_MS = 3500;
export const COMFORT_STAGE_LONG_DELAY_MS = 4500;
export const TRANSITION_STAGE_MIN_DELAY_MS = 800;
export const IMAGE_PRELOAD_TIMEOUT_MS = 20000;
export const IMAGE_PRELOAD_ERROR_MESSAGE = "画面还没靠岸，请返回重试";

export function getComfortStageDelayMs(text: string): number {
  const length = text.trim().length;
  if (length > COMFORT_STAGE_MEDIUM_MAX_LENGTH) {
    return COMFORT_STAGE_LONG_DELAY_MS;
  }
  if (length > COMFORT_STAGE_SHORT_MAX_LENGTH) {
    return COMFORT_STAGE_MEDIUM_DELAY_MS;
  }
  return COMFORT_STAGE_SHORT_DELAY_MS;
}

interface RevealStageSequenceOptions {
  comfortDelayMs: number;
  transitionDelayMs: number;
  imageReadyPromise: Promise<boolean>;
  waitForDelay: (delay: number) => Promise<void>;
  isCurrent: () => boolean;
  onTransitionStart: () => void;
  onRevealReady: () => void;
  onImageFailed: () => void;
}

export async function runRevealStageSequence({
  comfortDelayMs,
  transitionDelayMs,
  imageReadyPromise,
  waitForDelay,
  isCurrent,
  onTransitionStart,
  onRevealReady,
  onImageFailed,
}: RevealStageSequenceOptions): Promise<void> {
  await waitForDelay(comfortDelayMs);
  if (!isCurrent()) {
    return;
  }

  onTransitionStart();

  const [imageReady] = await Promise.all([imageReadyPromise, waitForDelay(transitionDelayMs)]);
  if (!isCurrent()) {
    return;
  }

  if (imageReady) {
    onRevealReady();
    return;
  }

  onImageFailed();
}

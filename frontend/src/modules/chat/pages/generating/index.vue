<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { useChatStore } from "@/modules/chat/store/chat";
import { CHAT_ASSETS } from "@/modules/chat/assets";
import ChatCabinScene from "@/modules/chat/components/ChatCabinScene.vue";
import ChatTicketRevealCard from "@/modules/chat/components/ChatTicketRevealCard.vue";
import { useSquareStore } from "@/modules/square/store/square";
import { createAsyncFlowGuard } from "@/modules/chat/utils/asyncFlowGuard";
import {
  IMAGE_PRELOAD_ERROR_MESSAGE,
  IMAGE_PRELOAD_TIMEOUT_MS,
  TRANSITION_STAGE_MIN_DELAY_MS,
  getComfortStageDelayMs,
  runRevealStageSequence,
} from "@/modules/chat/utils/generatingFlow";
import { canRerollCandidates, getNextRerollImageUrl, getRerollCandidates } from "@/modules/chat/utils/ticketReveal";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { ROUTES } from "@/shared/constants/routes";
import { getErrorMessage } from "@/shared/utils/error";
import { toChatHome, toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const chatStore = useChatStore();
const squareStore = useSquareStore();
const errorMsg = ref("");
const confirmLoading = ref(false);
const generatingStarted = ref(false);
const stageState = ref<"reply" | "transition" | "reveal">("reply");
const previewStage = ref<"" | "thinking" | "reply" | "transition" | "reveal">("");
const previewTicketUid = ref("");
const displayedResponseText = ref("");
const revealQueue = ref("");
const prefetchedRevealImageUrl = ref("");
const transitionTitleText = "海潮为你梳理着思绪……";
const transitionBodyText = "现在，它们正在被拓印成画，轻吟成诗……";
const generationFlowGuard = createAsyncFlowGuard();
let revealTimer: ReturnType<typeof setTimeout> | null = null;

const isFinished = computed(() => chatStore.generationState === "finished" && !!chatStore.ticketDraft);
const showReplyStage = computed(
  () =>
    previewStage.value === "reply" ||
    chatStore.generationState === "reply_streaming" ||
    chatStore.generationState === "asset_loading" ||
    (isFinished.value && stageState.value === "reply"),
);
const showTransitionStage = computed(
  () => previewStage.value === "transition" || (isFinished.value && stageState.value === "transition"),
);
const showRevealStage = computed(() => previewStage.value === "reveal" || (isFinished.value && stageState.value === "reveal"));
const ticketImageUrl = computed(() => chatStore.ticketDraft?.image_url ?? "");
const rerollCandidates = computed(() => getRerollCandidates(chatStore.ticketDraft?.candidate_images ?? []));
const canReroll = computed(() => canRerollCandidates(chatStore.ticketDraft?.candidate_images ?? [], confirmLoading.value));
const thinkingExcerptText = computed(() => {
  return chatStore.answer1.trim();
});
const responseText = computed(() => {
  const raw = chatStore.replyText?.trim();
  return raw || "";
});
const responseSubtitle = "让我为你用画面和诗句描绘现在的情绪";
const visibleResponseText = computed(() => displayedResponseText.value);
const displayError = computed(() => errorMsg.value || chatStore.streamError);

function normalizeError(error: unknown): string {
  return getErrorMessage(error, "请求失败，请稍后重试");
}

function goHome() {
  generationFlowGuard.invalidate();
  chatStore.resetSession();
  toChatHome();
}

function resetStageState() {
  stageState.value = "reply";
  prefetchedRevealImageUrl.value = "";
}

function clearRevealTimer() {
  if (!revealTimer) return;
  clearTimeout(revealTimer);
  revealTimer = null;
}

function getRevealChunkSize(queueLength: number): number {
  if (queueLength > 30) return 4;
  if (queueLength > 18) return 3;
  if (queueLength > 8) return 2;
  return 1;
}

function getRevealDelay(nextChunk: string): number {
  if (/[，。！？；：,.!?;:]$/.test(nextChunk)) return 70;
  return 28;
}

function runRevealLoop() {
  if (revealTimer || !revealQueue.value) return;

  const tick = () => {
    if (!revealQueue.value) {
      revealTimer = null;
      return;
    }

    const chunkSize = getRevealChunkSize(revealQueue.value.length);
    const nextChunk = revealQueue.value.slice(0, chunkSize);
    displayedResponseText.value += nextChunk;
    revealQueue.value = revealQueue.value.slice(chunkSize);

    revealTimer = setTimeout(tick, getRevealDelay(nextChunk));
  };

  revealTimer = setTimeout(tick, 28);
}

function flushRevealText() {
  if (revealQueue.value) {
    displayedResponseText.value += revealQueue.value;
    revealQueue.value = "";
  }
  clearRevealTimer();
}

function resetRevealText() {
  clearRevealTimer();
  displayedResponseText.value = "";
  revealQueue.value = "";
}

function waitForDelay(delay: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, delay);
  });
}

function preloadTicketImage(imageUrl: string) {
  if (!imageUrl) {
    return Promise.resolve(false);
  }

  return new Promise<boolean>((resolve) => {
    let settled = false;
    const timeout = setTimeout(() => {
      if (settled) return;
      settled = true;
      resolve(false);
    }, IMAGE_PRELOAD_TIMEOUT_MS);

    const finish = (result: boolean) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      resolve(result);
    };

    if (typeof Image !== "undefined") {
      const image = new Image();
      image.onload = () => finish(true);
      image.onerror = () => finish(false);
      image.src = imageUrl;
      return;
    }

    uni.getImageInfo({
      src: imageUrl,
      success: () => finish(true),
      fail: () => finish(false),
    });
  });
}

function startRevealFlow(token: number) {
  const currentImageUrl = chatStore.ticketDraft?.image_url ?? "";
  const imageReadyPromise = preloadTicketImage(currentImageUrl);

  errorMsg.value = "";
  prefetchedRevealImageUrl.value = "";

  void runRevealStageSequence({
    comfortDelayMs: getComfortStageDelayMs(responseText.value),
    transitionDelayMs: TRANSITION_STAGE_MIN_DELAY_MS,
    imageReadyPromise,
    waitForDelay,
    isCurrent: () => generationFlowGuard.isCurrent(token),
    onTransitionStart: () => {
      stageState.value = "transition";
      prefetchedRevealImageUrl.value = "";
      errorMsg.value = "";
    },
    onRevealReady: () => {
      stageState.value = "reveal";
      prefetchedRevealImageUrl.value = currentImageUrl;
      errorMsg.value = "";
    },
    onImageFailed: () => {
      stageState.value = "transition";
      prefetchedRevealImageUrl.value = "";
      errorMsg.value = IMAGE_PRELOAD_ERROR_MESSAGE;
    },
  });
}

async function beginGeneratingIfNeeded() {
  if (generatingStarted.value || !chatStore.pendingAnswer) return;

  const flowToken = generationFlowGuard.begin();
  generatingStarted.value = true;
  resetStageState();
  errorMsg.value = "";

  try {
    await chatStore.streamPendingAnswer();

    if (!generationFlowGuard.isCurrent(flowToken)) {
      return;
    }

    if (chatStore.generationState === "risk_blocked") {
      uni.redirectTo({ url: ROUTES.AID });
      return;
    }
    if (chatStore.generationState === "finished") {
      startRevealFlow(flowToken);
      return;
    }
  } catch (error) {
    if (!generationFlowGuard.isCurrent(flowToken)) {
      return;
    }
    errorMsg.value = normalizeError(error);
    generatingStarted.value = false;
  }
}

async function syncFlow() {
  errorMsg.value = "";

  if (previewStage.value === "thinking") return;
  if (previewStage.value === "reply") {
    stageState.value = "reply";
    return;
  }
  if (previewStage.value === "transition") {
    stageState.value = "transition";
    return;
  }
  if (previewStage.value === "reveal") {
    stageState.value = "reveal";
    return;
  }

  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  if (chatStore.generationState === "risk_blocked") {
    uni.redirectTo({ url: ROUTES.AID });
    return;
  }

  if (!chatStore.sessionId && !chatStore.ticketDraft && !chatStore.pendingAnswer) {
    toChatHome();
    return;
  }

  await beginGeneratingIfNeeded();

  if (isFinished.value) {
    if (!generatingStarted.value) {
      stageState.value = "reveal";
      prefetchedRevealImageUrl.value = ticketImageUrl.value;
    }
  }
}

function rerollCard() {
  if (!canReroll.value || !chatStore.ticketDraft) return;

  const nextImageUrl = getNextRerollImageUrl(chatStore.ticketDraft.image_url, chatStore.ticketDraft.candidate_images);
  if (!nextImageUrl) return;
  chatStore.chooseCandidate(nextImageUrl);
}

async function confirmCard() {
  if (confirmLoading.value) return;

  if (!chatStore.ticketDraft) {
    if (previewTicketUid.value) {
      uni.redirectTo({
        url: `${ROUTES.TICKET_DETAIL}?ticket_uid=${encodeURIComponent(previewTicketUid.value)}`,
      });
      return;
    }
    uni.showToast({ title: "当前没有可确认的船票", icon: "none" });
    return;
  }

  confirmLoading.value = true;
  errorMsg.value = "";

  try {
    const ticketUid = chatStore.ticketDraft.ticket_uid;
    squareStore.cacheSuggestedTags(ticketUid, chatStore.ticketDraft.recommended_tags);
    await chatStore.confirmTicketSelection();
    chatStore.resetSession();
    uni.redirectTo({
      url: `${ROUTES.TICKET_DETAIL}?ticket_uid=${encodeURIComponent(ticketUid)}`,
    });
  } catch (error) {
    errorMsg.value = normalizeError(error);
  } finally {
    confirmLoading.value = false;
  }
}

onLoad((options) => {
  const stage = options?.stage;
  previewTicketUid.value = (options?.ticket_uid as string) || "";
  if (stage === "thinking" || stage === "reply" || stage === "transition" || stage === "reveal") {
    previewStage.value = stage;
  }
});

onShow(() => {
  authStore.hydrateFromStorage();
  void syncFlow();
});

watch(
  () => responseText.value,
  (next) => {
    if (!next) {
      resetRevealText();
      return;
    }

    const consumedLength = displayedResponseText.value.length + revealQueue.value.length;
    const remaining = next.slice(consumedLength);
    if (!remaining) return;

    revealQueue.value += remaining;
    runRevealLoop();
  },
  { immediate: true },
);

watch(
  () => chatStore.generationState,
  (state) => {
    if (state === "asset_loading" || state === "finished" || state === "error" || state === "risk_blocked") {
      flushRevealText();
    }
    if (state === "processing") {
      resetRevealText();
    }
  },
);

onBeforeUnmount(() => {
  generationFlowGuard.invalidate();
  chatStore.cancelActiveChatWork(["reply_stream"]);
  generatingStarted.value = false;
  resetStageState();
  clearRevealTimer();
});
</script>

<template>
  <view class="chat-generating">
    <template v-if="showRevealStage">
      <StageViewportShell>
        <view class="chat-generating__inner">
          <view class="chat-generating__artboard">
            <ChatTicketRevealCard
              :image-url="ticketImageUrl"
              :prefetched-image-url="prefetchedRevealImageUrl"
              :refresh-icon="CHAT_ASSETS.icons.ticketRerollRefresh"
              :accept-disabled="confirmLoading"
              :accept-loading="confirmLoading"
              :reroll-disabled="!canReroll"
              @accept="confirmCard"
              @reroll="rerollCard"
            />

          <text v-if="displayError" class="chat-generating__error">{{ displayError }}</text>
          </view>
        </view>
      </StageViewportShell>
    </template>

    <ChatCabinScene
      v-else-if="showReplyStage"
      :show-prompt="false"
      stage-top="18.31%"
      :show-interaction="false"
      @back="goHome"
    >
      <template #after-stage>
        <view class="chat-generating__response-copy">
          <text class="chat-generating__response-text">{{ visibleResponseText }}</text>
          <text class="chat-generating__response-subtitle">{{ responseSubtitle }}</text>
        </view>
      </template>

      <template #footer>
        <text v-if="displayError" class="chat-generating__error">{{ displayError }}</text>
      </template>
    </ChatCabinScene>

    <ChatCabinScene
      v-else-if="showTransitionStage"
      :show-prompt="false"
      stage-top="18.31%"
      :show-interaction="false"
      @back="goHome"
    >
      <template #after-stage>
        <view class="chat-generating__transition-copy">
          <text class="chat-generating__transition-title">{{ transitionTitleText }}</text>
          <text class="chat-generating__transition-text">{{ transitionBodyText }}</text>
        </view>
      </template>

      <template #footer>
        <text v-if="displayError" class="chat-generating__error">{{ displayError }}</text>
      </template>
    </ChatCabinScene>

    <ChatCabinScene
      v-else
      :show-prompt="false"
      stage-top="25.29%"
      :show-interaction="false"
      @back="goHome"
    >
      <template #stage-overlay>
        <view class="chat-generating__deep-glow" />
      </template>

      <template #after-stage>
        <text class="chat-generating__title">让我想想……</text>

        <view class="chat-generating__excerpt-shell">
          <text class="chat-generating__excerpt-text">{{ thinkingExcerptText }}</text>
        </view>
      </template>

      <template #footer>
        <text v-if="displayError" class="chat-generating__error">{{ displayError }}</text>
      </template>
    </ChatCabinScene>
  </view>
</template>

<style scoped lang="scss">
.chat-generating {
  position: relative;
  min-height: 100vh;
}

.chat-generating__inner {
  position: relative;
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1;
}

.chat-generating__artboard {
  position: relative;
  width: min(100%, calc((100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) * 402 / 874));
  max-width: 804rpx;
  aspect-ratio: 402 / 874;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
}

.chat-generating__deep-glow {
  position: absolute;
  left: 6.97%;
  top: 17.62%;
  width: 96.02%;
  height: 44.16%;
  border-radius: 9999rpx;
  background: radial-gradient(
    circle at 50% 50%,
    rgba(203, 215, 194, 0.98) 0%,
    rgba(160, 214, 214, 0.68) 36%,
    rgba(116, 212, 234, 0.44) 68%,
    rgba(116, 212, 234, 0) 100%
  );
  filter: blur(64rpx);
  opacity: 0.96;
  transform: scale(1.02);
  animation: generating-deep-glow-breathe 5.6s ease-in-out infinite;
}

.chat-generating__response-copy {
  position: absolute;
  left: 0.37%;
  top: 44.62%;
  width: 99.25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 34rpx;
  text-align: center;
  z-index: 3;
}

.chat-generating__response-text {
  display: block;
  width: 99.25%;
  color: $anima-text-main;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
  white-space: pre-wrap;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
  font-family: $anima-font-display;
}

.chat-generating__response-subtitle {
  display: block;
  width: 99.25%;
  color: $anima-text-main;
  font-size: 36rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
  font-family: $anima-font-display;
}

.chat-generating__transition-copy {
  position: absolute;
  left: 0.37%;
  top: 51.37%;
  width: 99.25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14rpx;
  text-align: center;
  z-index: 3;
}

.chat-generating__transition-title {
  display: block;
  width: 99.25%;
  color: $anima-text-main;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
  font-family: $anima-font-display;
}

.chat-generating__transition-text {
  display: block;
  width: 99.25%;
  color: $anima-text-main;
  font-size: 36rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
  font-family: $anima-font-display;
}

.chat-generating__title {
  position: absolute;
  left: 50%;
  top: 17.28%;
  width: 240rpx;
  transform: translateX(-50%);
  color: $anima-text-main;
  font-size: 48rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
  font-family: $anima-font-display;
  z-index: 3;
  white-space: nowrap;
}

.chat-generating__excerpt-shell {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 60.2%;
  transform: translateX(-50%);
  text-align: center;
  z-index: 3;
}

.chat-generating__excerpt-text {
  display: block;
  width: 100%;
  color: rgba(224, 240, 255, 0.52);
  font-size: 24rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
  white-space: pre-wrap;
  text-shadow: 0 0 8rpx rgba(230, 248, 255, 0.1);
  filter: blur(1rpx);
  font-family: $anima-font-display;
}

.chat-generating__error {
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 7%;
  color: $anima-text-error;
  font-size: 24rpx;
  line-height: 1.7;
  text-align: center;
  z-index: 5;
}

@keyframes generating-deep-glow-breathe {
  0%,
  100% {
    opacity: 0.9;
    transform: scale(1.01);
  }

  50% {
    opacity: 1;
    transform: scale(1.06);
  }
}
</style>

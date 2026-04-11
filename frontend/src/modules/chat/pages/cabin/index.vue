<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import ChatCabinScene from "@/modules/chat/components/ChatCabinScene.vue";
import CabinTextInputBlock from "@/modules/chat/components/CabinTextInputBlock.vue";
import { useAuthStore } from "@/modules/auth/store/auth";
import { useChatStore } from "@/modules/chat/store/chat";
import { createAsyncFlowGuard } from "@/modules/chat/utils/asyncFlowGuard";
import { isRequestAbortedError } from "@/infrastructure/http/request";
import { ROUTES } from "@/shared/constants/routes";
import { ApiError } from "@/shared/types/http";
import { toChatHome, toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const chatStore = useChatStore();
const cabinAsyncGuard = createAsyncFlowGuard();

const inputValue = ref("");
const errorMsg = ref("");
const freshOpen = ref(false);
const sceneTransitioning = ref(false);
const cabinFlow = ref<"first" | "submitted-preview" | "second">("first");
const cabinUiState = ref<"prompt" | "focus" | "typing">("prompt");
const currentQuestionIndex = ref<1 | 2>(1);
const cabinPromptText = ref("");
const secondPromptText = ref("");
const submittedPreviewText = ref("");

const placeholderText = computed(() => "这一刻，想写下什么…");

const estimatedLineCount = computed(() => {
  if (!inputValue.value.trim()) return 1;
  const lines = inputValue.value.split("\n");
  return lines.reduce((count, line) => {
    const textLength = line.length || 1;
    return count + Math.max(1, Math.ceil(textLength / 10));
  }, 0);
});

const showPrompt = computed(() => cabinFlow.value === "first" && cabinUiState.value === "prompt");
const showVoiceIcon = computed(() => cabinFlow.value !== "submitted-preview" && cabinUiState.value !== "typing");
const interactionTop = computed(() => {
  if (cabinFlow.value === "submitted-preview") return "47.94%";
  if (cabinFlow.value === "second") return "56.75%";
  if (cabinUiState.value === "prompt") return "57.21%";
  if (cabinUiState.value === "focus") return "48.05%";
  return "47.94%";
});
const interactionLeft = computed(() => {
  if (cabinFlow.value === "submitted-preview") return "10.45%";
  if (cabinFlow.value === "second") return "13.18%";
  return cabinUiState.value === "typing" ? "10.45%" : "13.18%";
});
const interactionWidth = computed(() => (cabinFlow.value === "submitted-preview" ? "81.09%" : "78.36%"));
const clampedLineCount = computed(() => Math.min(Math.max(estimatedLineCount.value, 1), 4));
const textareaHeight = computed(() => {
  if (cabinFlow.value === "submitted-preview") return "224rpx";
  return `${clampedLineCount.value * 56 + 14}rpx`;
});
const inputMinHeight = computed(() => {
  if (cabinFlow.value === "submitted-preview") return "224rpx";
  if (cabinFlow.value === "second") return "90rpx";
  return textareaHeight.value;
});
const focusInput = computed(() => cabinFlow.value !== "submitted-preview" && cabinUiState.value !== "prompt");
const showCenterText = computed(() => cabinFlow.value === "second");
const composerGap = computed(() => (cabinFlow.value === "second" ? "46rpx" : "64rpx"));
const inputDisabled = computed(() => chatStore.loading || cabinFlow.value === "submitted-preview");
const showSubmit = computed(() => cabinFlow.value !== "submitted-preview");
const activeModelValue = computed(() => (cabinFlow.value === "submitted-preview" ? submittedPreviewText.value : inputValue.value));
const activePlaceholder = computed(() => (cabinFlow.value === "submitted-preview" ? "" : placeholderText.value));

function normalizeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    return JSON.stringify(error.detail);
  }
  return "请求失败，请稍后重试";
}

async function ensureSession() {
  if (chatStore.sessionId) return;
  await chatStore.startSession();
}

function resetCabinFlow() {
  inputValue.value = "";
  errorMsg.value = "";
  cabinFlow.value = "first";
  cabinUiState.value = "prompt";
  currentQuestionIndex.value = 1;
  cabinPromptText.value = "";
  submittedPreviewText.value = "";
  secondPromptText.value = "";
}

onLoad((options) => {
  freshOpen.value = options?.fresh === "1";
});

onShow(async () => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  errorMsg.value = "";
  try {
    if (freshOpen.value) {
      chatStore.resetSession();
      resetCabinFlow();
      freshOpen.value = false;
    } else if (chatStore.ticketDraft || chatStore.step >= 2) {
      chatStore.resetSession();
      resetCabinFlow();
    }
    if (!chatStore.sessionId && !freshOpen.value) {
      resetCabinFlow();
    }
    await ensureSession();
    cabinPromptText.value = chatStore.q1 ? `“${chatStore.q1}”` : "";
    if (chatStore.step === 1) {
      cabinFlow.value = "second";
      currentQuestionIndex.value = 2;
      secondPromptText.value = chatStore.q2 || "";
    }
  } catch (error) {
    errorMsg.value = normalizeError(error);
  }
});

onBeforeUnmount(() => {
  cabinAsyncGuard.invalidate();
  chatStore.cancelActiveChatWork(["q1_submit"]);
});

async function submitAnswer() {
  const content = inputValue.value.trim();
  if (!content || chatStore.loading) return;
  const actionToken = cabinAsyncGuard.begin();

  errorMsg.value = "";
  try {
    await ensureSession();

    const isFirstAnswer = currentQuestionIndex.value === 1;
    if (isFirstAnswer) {
      submittedPreviewText.value = content;
      cabinFlow.value = "submitted-preview";
      cabinUiState.value = "typing";
    }

    if (isFirstAnswer) {
      const previewStart = Date.now();
      await chatStore.submitAnswer(content);

      if (!cabinAsyncGuard.isCurrent(actionToken)) {
        return;
      }

      if (chatStore.generationState === "risk_blocked") {
        uni.navigateTo({ url: ROUTES.AID });
        return;
      }

      const elapsed = Date.now() - previewStart;
      const previewDelay = Math.max(0, 1200 - elapsed);
      if (previewDelay > 0) {
        await new Promise((resolve) => setTimeout(resolve, previewDelay));
      }
      sceneTransitioning.value = true;
      await new Promise((resolve) => setTimeout(resolve, 180));
      inputValue.value = "";
      cabinFlow.value = "second";
      cabinUiState.value = "prompt";
      currentQuestionIndex.value = 2;
      secondPromptText.value = chatStore.q2 || "";
      await nextTick();
      if (!cabinAsyncGuard.isCurrent(actionToken)) {
        return;
      }
      sceneTransitioning.value = false;
      return;
    }

    chatStore.queueFinalAnswer(content);
    inputValue.value = "";
    cabinAsyncGuard.invalidate();
    uni.redirectTo({ url: ROUTES.CHAT_GENERATING });
  } catch (error) {
    if (!cabinAsyncGuard.isCurrent(actionToken) || isRequestAbortedError(error)) {
      return;
    }
    errorMsg.value = normalizeError(error);
  }
}

function goBack() {
  cabinAsyncGuard.invalidate();
  chatStore.cancelActiveChatWork(["q1_submit"]);
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }
  toChatHome();
}

function onFocusComposer() {
  if (cabinFlow.value === "submitted-preview") return;
  if (cabinUiState.value === "prompt") {
    cabinUiState.value = "focus";
  }
}

function onInputValue(value: string) {
  inputValue.value = value;
  if (cabinFlow.value === "submitted-preview") return;
  cabinUiState.value = value.trim() && estimatedLineCount.value > 1 ? "typing" : "focus";
}

function openVoiceInput() {
  cabinAsyncGuard.invalidate();
  chatStore.cancelActiveChatWork(["q1_submit"]);
  uni.navigateTo({ url: ROUTES.CHAT_VOICE });
}
</script>

<template>
  <ChatCabinScene
    :prompt-text="cabinPromptText"
    :show-prompt="showPrompt"
    :show-center-text="showCenterText"
    :center-text="secondPromptText"
    :interaction-top="interactionTop"
    :interaction-left="interactionLeft"
    :interaction-width="interactionWidth"
    :transitioning="sceneTransitioning"
    @back="goBack"
  >
    <template #interaction>
      <CabinTextInputBlock
        :model-value="activeModelValue"
        :placeholder="activePlaceholder"
        :show-voice-icon="showVoiceIcon"
        :show-submit="showSubmit"
        :submit-label="chatStore.loading ? '发送中' : '写好了'"
        :input-disabled="inputDisabled"
        :submit-disabled="chatStore.loading || !inputValue.trim()"
        :composer-gap="composerGap"
        :input-min-height="inputMinHeight"
        :textarea-height="textareaHeight"
        :input-max-length="200"
        :focus-input="focusInput"
        :transitioning="sceneTransitioning"
        @focus="onFocusComposer"
        @voice="openVoiceInput"
        @submit="submitAnswer"
        @update:model-value="onInputValue"
      />
    </template>
    <template #footer>
      <text v-if="errorMsg" class="chat-cabin__error">{{ errorMsg }}</text>
    </template>
  </ChatCabinScene>
</template>

<style scoped lang="scss">
.chat-cabin__error {
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 6%;
  color: var(--anima-text-error);
  font-size: 24rpx;
  text-align: center;
  z-index: 4;
}
</style>

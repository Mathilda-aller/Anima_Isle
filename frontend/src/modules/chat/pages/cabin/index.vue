<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import ChatCabinScene from "@/modules/chat/components/ChatCabinScene.vue";
import CabinTextInputBlock from "@/modules/chat/components/CabinTextInputBlock.vue";
import ChatDailyLimitModal from "@/modules/chat/components/ChatDailyLimitModal.vue";
import { useAuthStore } from "@/modules/auth/store/auth";
import { useChatStore } from "@/modules/chat/store/chat";
import { ROUTES } from "@/shared/constants/routes";
import { ApiError } from "@/shared/types/http";
import { getErrorMessage } from "@/shared/utils/error";
import { toChatHome, toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const chatStore = useChatStore();

const inputValue = ref("");
const errorMsg = ref("");
const freshOpen = ref(false);
const dailyLimitModalVisible = ref(false);
const cabinUiState = ref<"prompt" | "focus" | "typing">("prompt");
const cabinPromptText = ref("");

const placeholderText = computed(() => "这一刻，想写下什么…");

const estimatedLineCount = computed(() => {
  if (!inputValue.value.trim()) return 1;
  const lines = inputValue.value.split("\n");
  return lines.reduce((count, line) => {
    const textLength = line.length || 1;
    return count + Math.max(1, Math.ceil(textLength / 10));
  }, 0);
});

const showPrompt = computed(() => true);
const showVoiceIcon = computed(() => cabinUiState.value !== "typing");
const interactionTop = computed(() => {
  if (cabinUiState.value === "prompt") return "57.21%";
  if (cabinUiState.value === "focus") return "48.05%";
  return "47.94%";
});
const interactionLeft = computed(() => (cabinUiState.value === "typing" ? "10.45%" : "13.18%"));
const interactionWidth = computed(() => "78.36%");
const clampedLineCount = computed(() => Math.min(Math.max(estimatedLineCount.value, 1), 4));
const textareaHeight = computed(() => `${clampedLineCount.value * 56 + 14}rpx`);
const inputMinHeight = computed(() => textareaHeight.value);
const focusInput = computed(() => cabinUiState.value !== "prompt");
const composerGap = computed(() => "64rpx");
const inputDisabled = computed(() => chatStore.loading);

function normalizeError(error: unknown): string {
  return getErrorMessage(error, "请求失败，请稍后重试");
}

function isDailyTicketLimitError(error: unknown): boolean {
  return error instanceof ApiError && error.statusCode === 429 && error.detail === "daily_ticket_limit_reached";
}

function showDailyLimitModal() {
  if (dailyLimitModalVisible.value) return;
  dailyLimitModalVisible.value = true;
}

function handleDailyLimitConfirm() {
  dailyLimitModalVisible.value = false;
  goBack();
}

async function ensureSession() {
  if (chatStore.sessionId) return;
  await chatStore.startSession();
}

function resetCabinFlow() {
  inputValue.value = "";
  errorMsg.value = "";
  cabinUiState.value = "prompt";
  cabinPromptText.value = "";
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
  } catch (error) {
    if (isDailyTicketLimitError(error)) {
      showDailyLimitModal();
      return;
    }
    errorMsg.value = normalizeError(error);
  }
});

async function submitAnswer() {
  const content = inputValue.value.trim();
  if (!content || chatStore.loading) return;

  errorMsg.value = "";
  try {
    await ensureSession();
    chatStore.queuePendingAnswer(content);
    inputValue.value = "";
    uni.redirectTo({ url: ROUTES.CHAT_GENERATING });
  } catch (error) {
    errorMsg.value = normalizeError(error);
  }
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }
  toChatHome();
}

function onFocusComposer() {
  if (cabinUiState.value === "prompt") {
    cabinUiState.value = "focus";
  }
}

function onInputValue(value: string) {
  inputValue.value = value;
  cabinUiState.value = value.trim() && estimatedLineCount.value > 1 ? "typing" : "focus";
}

function openVoiceInput() {
  uni.navigateTo({ url: ROUTES.CHAT_VOICE });
}
</script>

<template>
  <ChatCabinScene
    :prompt-text="cabinPromptText"
    :show-prompt="showPrompt"
    :interaction-top="interactionTop"
    :interaction-left="interactionLeft"
    :interaction-width="interactionWidth"
    @back="goBack"
  >
    <template #interaction>
      <CabinTextInputBlock
        :model-value="inputValue"
        :placeholder="placeholderText"
        :show-voice-icon="showVoiceIcon"
        :submit-label="chatStore.loading ? '发送中' : '写好了'"
        :input-disabled="inputDisabled"
        :submit-disabled="chatStore.loading || !inputValue.trim()"
        :composer-gap="composerGap"
        :input-min-height="inputMinHeight"
        :textarea-height="textareaHeight"
        :input-max-length="200"
        :focus-input="focusInput"
        @focus="onFocusComposer"
        @voice="openVoiceInput"
        @submit="submitAnswer"
        @update:model-value="onInputValue"
      />
    </template>
    <template #footer>
      <text v-if="errorMsg" class="chat-cabin__error">{{ errorMsg }}</text>
      <ChatDailyLimitModal v-if="dailyLimitModalVisible" @confirm="handleDailyLimitConfirm" />
    </template>
  </ChatCabinScene>
</template>

<style scoped lang="scss">
.chat-cabin__error {
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 6%;
  color: $anima-text-error;
  font-size: 24rpx;
  text-align: center;
  z-index: 4;
}
</style>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { transcribeVoiceCancelable } from "@/modules/chat/api/chat";
import { isRequestAbortedError } from "@/infrastructure/http/request";
import { useChatStore } from "@/modules/chat/store/chat";
import ChatCabinScene from "@/modules/chat/components/ChatCabinScene.vue";
import ChatDailyLimitModal from "@/modules/chat/components/ChatDailyLimitModal.vue";
import CabinVoiceControlBlock from "@/modules/chat/components/CabinVoiceControlBlock.vue";
import { createAsyncFlowGuard } from "@/modules/chat/utils/asyncFlowGuard";
import { ROUTES } from "@/shared/constants/routes";
import { ApiError } from "@/shared/types/http";
import { toChatHome, toLogin } from "@/shared/utils/navigation";

interface SpeechRecognitionAlternativeLike {
  transcript: string;
}

interface SpeechRecognitionResultLike {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternativeLike;
  [index: number]: SpeechRecognitionAlternativeLike;
}

interface SpeechRecognitionEventLike extends Event {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: SpeechRecognitionResultLike;
  };
}

interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: Event & { error?: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

interface BrowserSpeechRecognitionCtor {
  new (): SpeechRecognitionLike;
}

const authStore = useAuthStore();
const chatStore = useChatStore();
const voiceAsyncGuard = createAsyncFlowGuard();
const voiceUiState = ref<"idle" | "recording" | "transcribing" | "review">("idle");
const isRecording = ref(false);
const elapsedSeconds = ref(0);
const freshOpen = ref(false);
const permissionState = ref<"idle" | "granted" | "denied" | "unsupported">("idle");
const rippleIntensity = ref(0);
const errorMsg = ref("");
const dailyLimitModalVisible = ref(false);
const sceneTransitioning = ref(false);
const voiceFlow = ref<"first" | "second">("first");
const currentQuestionIndex = ref<1 | 2>(1);
const transcriptPreviewText = ref("");
const voicePromptText = ref("");
const listeningPromptText = ref("我在听……");
const transcribingPromptText = ref("正在整理你的声音……");
const secondVoicePromptText = ref("");
const reviewTranscriptText = ref("");
const recordedAudioBlob = ref<Blob | null>(null);
let mediaRecorder: MediaRecorder | null = null;
let mediaStream: MediaStream | null = null;
let audioContext: AudioContext | null = null;
let analyserNode: AnalyserNode | null = null;
let sourceNode: MediaStreamAudioSourceNode | null = null;
let speechRecognition: SpeechRecognitionLike | null = null;
let analyserFrame = 0;
let recordTimer: ReturnType<typeof setInterval> | null = null;
let recordStartedAt = 0;
let recordedChunks: BlobPart[] = [];
let transcribeFailed = false;

const durationText = computed(() => {
  const minutes = String(Math.floor(elapsedSeconds.value / 60)).padStart(2, "0");
  const seconds = String(elapsedSeconds.value % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
});
const currentQuestionPromptText = computed(() => (
  voiceFlow.value === "second" ? secondVoicePromptText.value : voicePromptText.value
));

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
      resetVoiceFlow();
      freshOpen.value = false;
    } else if (chatStore.ticketDraft || chatStore.step >= 2) {
      chatStore.resetSession();
      resetVoiceFlow();
    } else if (!chatStore.sessionId) {
      resetVoiceFlow();
    }

    await ensureSession();
    voicePromptText.value = chatStore.q1 ? `“${chatStore.q1}”` : "";

    if (chatStore.step === 1) {
      voiceFlow.value = "second";
      currentQuestionIndex.value = 2;
      secondVoicePromptText.value = chatStore.q2 || "";
    }
  } catch (error) {
    if (isDailyTicketLimitError(error)) {
      showDailyLimitModal();
      return;
    }
    errorMsg.value = normalizeError(error);
  }
});

onBeforeUnmount(() => {
  voiceAsyncGuard.invalidate();
  chatStore.cancelActiveChatWork(["voice_transcribe", "q1_submit"]);
  stopRecordingTimer();
  void releaseMediaStream();
  stopAnalyserLoop();
  stopSpeechRecognition();
});

const scenePromptText = computed(() => {
  if (voiceUiState.value === "recording") return listeningPromptText.value;
  if (voiceUiState.value === "transcribing") return transcribingPromptText.value;
  return currentQuestionPromptText.value;
});
const showCenterText = computed(() => {
  if (voiceUiState.value === "recording" || voiceUiState.value === "transcribing") {
    return Boolean(transcriptPreviewText.value.trim());
  }
  if (voiceUiState.value === "review") {
    return Boolean(reviewTranscriptText.value.trim());
  }
  return false;
});
const sceneCenterText = computed(() => {
  if (voiceUiState.value === "review") return reviewTranscriptText.value;
  if (voiceUiState.value === "recording" || voiceUiState.value === "transcribing") {
    return transcriptPreviewText.value;
  }
  return "";
});
const scenePromptTop = computed(() => (
  voiceUiState.value === "recording" || voiceUiState.value === "transcribing" ? "18.31%" : "44.05%"
));
const sceneCenterTop = computed(() => "51.14%");
const stageTop = computed(() => (
  voiceUiState.value === "recording" || voiceUiState.value === "transcribing" ? "25.29%" : "16.25%"
));
const interactionTop = computed(() => (
  voiceUiState.value === "review" ? "" : voiceUiState.value === "recording" || voiceUiState.value === "transcribing" ? "58.35%" : "66.93%"
));
const interactionBottom = computed(() => (
  voiceUiState.value === "review" ? "calc(4.2% + env(safe-area-inset-bottom))" : ""
));
const interactionLeft = computed(() => (
  voiceUiState.value === "recording" || voiceUiState.value === "transcribing" ? "-1.74%" : "4%"
));
const interactionWidth = computed(() => (
  voiceUiState.value === "review" ? "92%" : voiceUiState.value === "recording" || voiceUiState.value === "transcribing" ? "103.48%" : "92%"
));
const showReviewActions = computed(() => voiceUiState.value === "review");
const showPrimaryControls = computed(() => voiceUiState.value !== "review");
const showWriteEntry = computed(() => voiceUiState.value === "idle");
const showMeta = computed(() => voiceUiState.value === "transcribing" || voiceUiState.value === "review");
const controlStatusText = computed(() => {
  if (voiceUiState.value === "transcribing") return "正在整理你的声音…";
  if (voiceUiState.value === "review") return "确认这段话后发送";
  if (voiceUiState.value === "recording") return "正在倾听你的声音";
  return "轻触开始说话";
});

function normalizeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    return JSON.stringify(error.detail);
  }
  return "录音处理失败，请稍后重试";
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

function resetVoiceFlow() {
  errorMsg.value = "";
  voiceFlow.value = "first";
  voiceUiState.value = "idle";
  currentQuestionIndex.value = 1;
  voicePromptText.value = "";
  secondVoicePromptText.value = "";
  transcriptPreviewText.value = "";
  reviewTranscriptText.value = "";
  recordedAudioBlob.value = null;
  transcribeFailed = false;
  elapsedSeconds.value = 0;
  rippleIntensity.value = 0;
}

function goBack() {
  voiceAsyncGuard.invalidate();
  chatStore.cancelActiveChatWork(["voice_transcribe", "q1_submit"]);
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }
  toChatHome();
}

async function toggleRecording() {
  errorMsg.value = "";
  try {
    if (voiceUiState.value === "transcribing") {
      return;
    }
    if (voiceUiState.value === "review") {
      await restartRecording();
      return;
    }
    if (isRecording.value) {
      await stopRecording();
      return;
    }
    await startRecording();
  } catch (error) {
    errorMsg.value = normalizeError(error);
  }
}

function clearReviewState() {
  transcriptPreviewText.value = "";
  reviewTranscriptText.value = "";
  recordedAudioBlob.value = null;
  transcribeFailed = false;
}

async function restartRecording() {
  errorMsg.value = "";
  isRecording.value = false;
  voiceUiState.value = "idle";
  elapsedSeconds.value = 0;
  rippleIntensity.value = 0;
  stopRecordingTimer();
  clearReviewState();
}

async function cancelRecording() {
  errorMsg.value = "";
  try {
    if (isRecording.value) {
      await stopRecording(true);
    }
  } catch (error) {
    errorMsg.value = normalizeError(error);
  }
  await restartRecording();
  uni.showToast({ title: "已取消录音", icon: "none" });
}

async function submitReview() {
  const submittedText = reviewTranscriptText.value.trim();
  if (!submittedText || voiceUiState.value !== "review") return;
  const actionToken = voiceAsyncGuard.begin();

  errorMsg.value = "";

  try {
    await ensureSession();

    if (currentQuestionIndex.value === 1) {
      await chatStore.submitAnswer(submittedText, {
        isVoice: true,
        duration: elapsedSeconds.value,
      });

      if (!voiceAsyncGuard.isCurrent(actionToken)) {
        return;
      }

      if (chatStore.generationState === "risk_blocked") {
        uni.navigateTo({ url: ROUTES.AID });
        return;
      }

      await transitionToSecondQuestion(actionToken);
      return;
    }

    chatStore.queueFinalAnswer(submittedText, {
      isVoice: true,
      duration: elapsedSeconds.value,
    });
    clearReviewState();
    voiceAsyncGuard.invalidate();
    uni.redirectTo({ url: ROUTES.CHAT_GENERATING });
  } catch (error) {
    if (!voiceAsyncGuard.isCurrent(actionToken) || isRequestAbortedError(error)) {
      return;
    }
    errorMsg.value = normalizeError(error);
  }
}

function openTextInput() {
  voiceAsyncGuard.invalidate();
  chatStore.cancelActiveChatWork(["voice_transcribe", "q1_submit"]);
  const pages = getCurrentPages();
  const previousPage = pages[pages.length - 2];
  if (previousPage?.route === ROUTES.CHAT_CABIN.replace(/^\//, "")) {
    uni.navigateBack();
    return;
  }
  uni.navigateTo({ url: `${ROUTES.CHAT_CABIN}?fresh=1` });
}

function startRecordingTimer() {
  stopRecordingTimer();
  recordStartedAt = Date.now();
  recordTimer = setInterval(() => {
    elapsedSeconds.value = Math.max(0, Math.floor((Date.now() - recordStartedAt) / 1000));
  }, 1000);
}

function stopRecordingTimer() {
  if (!recordTimer) return;
  clearInterval(recordTimer);
  recordTimer = null;
}

async function startRecording() {
  const supported = await ensureRecorderReady();
  if (!supported || !mediaRecorder) return;

  recordedAudioBlob.value = null;
  recordedChunks = [];
  transcribeFailed = false;
  elapsedSeconds.value = 0;
  transcriptPreviewText.value = "";
  reviewTranscriptText.value = "";

  mediaRecorder.start(250);
  startSpeechRecognition();
  isRecording.value = true;
  voiceUiState.value = "recording";
  startRecordingTimer();
  startAnalyserLoop();
}

async function stopRecording(discard = false) {
  if (!mediaRecorder || mediaRecorder.state === "inactive") {
    isRecording.value = false;
    stopRecordingTimer();
    await releaseMediaStream();
    return;
  }

  const currentRecorder = mediaRecorder;
  if (!currentRecorder) return;

  const blob = await new Promise<Blob | null>((resolve) => {
    const finalizeBlob = () => {
      currentRecorder.onstop = null;
      const nextBlob = discard || !recordedChunks.length
        ? null
        : new Blob(recordedChunks, { type: currentRecorder.mimeType || "audio/webm" });
      resolve(nextBlob);
    };

    currentRecorder.onstop = () => {
      // Some browsers flush the last audio chunk on stop; defer blob assembly
      // to the next task so ondataavailable has a chance to run first.
      setTimeout(finalizeBlob, 0);
    };
    if (typeof currentRecorder.requestData === "function") {
      try {
        currentRecorder.requestData();
      } catch (error) {
        console.error("media_recorder_request_data_failed", error);
      }
    }
    currentRecorder.stop();
  });

  recordedAudioBlob.value = blob;
  isRecording.value = false;
  voiceUiState.value = "transcribing";
  rippleIntensity.value = 0;
  stopRecordingTimer();
  stopAnalyserLoop();
  stopSpeechRecognition();
  await releaseMediaStream();

  if (discard || !blob) return;

  const transcribeToken = voiceAsyncGuard.begin();
  const submittedText = await transcribeRecordedAudio(blob);
  if (!voiceAsyncGuard.isCurrent(transcribeToken)) {
    return;
  }
  if (!submittedText) {
    voiceUiState.value = "idle";
    if (!transcribeFailed) {
      errorMsg.value = "没有识别到语音内容，请再试一次";
    }
    return;
  }

  transcriptPreviewText.value = submittedText;
  reviewTranscriptText.value = submittedText;
  voiceUiState.value = "review";
}

async function ensureRecorderReady(): Promise<boolean> {
  if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    permissionState.value = "unsupported";
    uni.showToast({ title: "当前环境暂不支持录音", icon: "none" });
    return false;
  }

  if (mediaRecorder && mediaStream) {
    return true;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    permissionState.value = "granted";
    mediaRecorder = new MediaRecorder(mediaStream);
    setupAudioAnalyser(mediaStream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };
    mediaRecorder.onerror = () => {
      uni.showToast({ title: "录音过程中断", icon: "none" });
    };
    return true;
  } catch (error) {
    console.error("microphone_permission_failed", error);
    permissionState.value = "denied";
    uni.showToast({ title: "请先允许麦克风权限", icon: "none" });
    return false;
  }
}

async function releaseMediaStream() {
  stopAnalyserLoop();
  if (sourceNode) {
    sourceNode.disconnect();
  }
  if (analyserNode) {
    analyserNode.disconnect();
  }
  if (audioContext && audioContext.state !== "closed") {
    await audioContext.close();
  }
  sourceNode = null;
  analyserNode = null;
  audioContext = null;
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
  }
  mediaStream = null;
  mediaRecorder = null;
}

async function ensureSession() {
  if (chatStore.sessionId) return;
  await chatStore.startSession();
}

async function transcribeRecordedAudio(blob: Blob): Promise<string> {
  await ensureSession();
  transcribeFailed = false;
  const sessionId = chatStore.sessionId;
  const requestMeta = chatStore.beginTrackedRequest("voice_transcribe", sessionId);
  const formData = new FormData();
  formData.append("file", blob, `question-${currentQuestionIndex.value}.webm`);
  formData.append("session_id", chatStore.sessionId);
  formData.append("question_index", String(currentQuestionIndex.value));
  formData.append("duration", String(elapsedSeconds.value));

  try {
    const operation = transcribeVoiceCancelable(formData);
    chatStore.attachTrackedRequestCancel("voice_transcribe", requestMeta.token, sessionId, operation.cancel);
    const result = await operation.promise;
    if (!chatStore.isTrackedRequestCurrent("voice_transcribe", requestMeta.token, sessionId)) {
      return "";
    }
    return result.text.trim();
  } catch (error) {
    if (isRequestAbortedError(error) || !chatStore.isTrackedRequestCurrent("voice_transcribe", requestMeta.token, sessionId)) {
      return "";
    }
    console.error("voice_transcribe_failed", error);
    transcribeFailed = true;
    errorMsg.value = normalizeError(error);
    voiceUiState.value = "idle";
    return "";
  } finally {
    chatStore.finishTrackedRequest("voice_transcribe", requestMeta.token, sessionId);
  }
}

function setupAudioAnalyser(stream: MediaStream) {
  if (typeof window === "undefined") return;
  const AudioContextCtor = window.AudioContext || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextCtor) return;

  audioContext = new AudioContextCtor();
  analyserNode = audioContext.createAnalyser();
  analyserNode.fftSize = 1024;
  analyserNode.smoothingTimeConstant = 0.82;
  sourceNode = audioContext.createMediaStreamSource(stream);
  sourceNode.connect(analyserNode);
}

function startAnalyserLoop() {
  if (!analyserNode) return;
  stopAnalyserLoop();
  const samples = new Uint8Array(analyserNode.fftSize);

  const tick = () => {
    if (!analyserNode || !isRecording.value) return;
    analyserNode.getByteTimeDomainData(samples);
    let sum = 0;
    for (let i = 0; i < samples.length; i += 1) {
      const normalized = (samples[i] - 128) / 128;
      sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / samples.length);
    const nextIntensity = Math.min(1, Math.max(0, (rms - 0.015) / 0.13));
    rippleIntensity.value = rippleIntensity.value * 0.7 + nextIntensity * 0.3;
    analyserFrame = requestAnimationFrame(tick);
  };

  analyserFrame = requestAnimationFrame(tick);
}

function stopAnalyserLoop() {
  if (analyserFrame) {
    cancelAnimationFrame(analyserFrame);
    analyserFrame = 0;
  }
  rippleIntensity.value = 0;
}

async function transitionToSecondQuestion(actionToken: number) {
  errorMsg.value = "";
  sceneTransitioning.value = true;
  await new Promise((resolve) => setTimeout(resolve, 220));
  if (!voiceAsyncGuard.isCurrent(actionToken)) {
    return;
  }
  voiceFlow.value = "second";
  voiceUiState.value = "idle";
  currentQuestionIndex.value = 2;
  secondVoicePromptText.value = chatStore.q2 || "";
  elapsedSeconds.value = 0;
  clearReviewState();
  await new Promise((resolve) => setTimeout(resolve, 80));
  if (!voiceAsyncGuard.isCurrent(actionToken)) {
    return;
  }
  sceneTransitioning.value = false;
}

function startSpeechRecognition() {
  if (typeof window === "undefined") return;
  const RecognitionCtor =
    (window as Window & { SpeechRecognition?: BrowserSpeechRecognitionCtor; webkitSpeechRecognition?: BrowserSpeechRecognitionCtor }).SpeechRecognition
    || (window as Window & { webkitSpeechRecognition?: BrowserSpeechRecognitionCtor }).webkitSpeechRecognition;

  if (!RecognitionCtor) {
    if (!transcriptPreviewText.value) {
      transcriptPreviewText.value = "当前浏览器暂不支持实时转写";
    }
    return;
  }

  stopSpeechRecognition();
  speechRecognition = new RecognitionCtor();
  speechRecognition.continuous = true;
  speechRecognition.interimResults = true;
  speechRecognition.lang = "zh-CN";

  speechRecognition.onresult = (event) => {
    let finalText = "";
    let interimText = "";
    for (let i = 0; i < event.results.length; i += 1) {
      const result = event.results[i];
      const transcript = result[0]?.transcript || result.item(0)?.transcript || "";
      if (result.isFinal) {
        finalText += transcript;
      } else {
        interimText += transcript;
      }
    }
    transcriptPreviewText.value = `${finalText}${interimText}`.trim();
  };

  speechRecognition.onerror = (event) => {
    if (event.error === "not-allowed") {
      errorMsg.value = "请先允许语音识别权限";
      return;
    }
    if (event.error === "no-speech") {
      return;
    }
    errorMsg.value = "语音识别中断，请重试";
  };

  speechRecognition.onend = () => {
    speechRecognition = null;
  };

  try {
    speechRecognition.start();
  } catch (error) {
    console.error("speech_recognition_start_failed", error);
  }
}

function stopSpeechRecognition() {
  if (!speechRecognition) return;
  try {
    speechRecognition.stop();
  } catch (error) {
    console.error("speech_recognition_stop_failed", error);
  }
  speechRecognition = null;
}
</script>

<template>
  <ChatCabinScene
    :prompt-text="scenePromptText"
    :show-prompt="true"
    :show-center-text="showCenterText"
    :center-text="sceneCenterText"
    center-variant="transcript"
    :stage-top="stageTop"
    :prompt-top="scenePromptTop"
    :center-top="sceneCenterTop"
    :interaction-top="interactionTop"
    :interaction-bottom="interactionBottom"
    :interaction-left="interactionLeft"
    :interaction-width="interactionWidth"
    :transitioning="sceneTransitioning"
    @back="goBack"
  >
    <template #interaction>
      <CabinVoiceControlBlock
        :recording="isRecording"
        :processing="voiceUiState === 'transcribing'"
        :ripple-intensity="rippleIntensity"
        :show-meta="showMeta"
        :show-actions="showReviewActions"
        :show-primary-controls="showPrimaryControls"
        :show-write-entry="showWriteEntry"
        :status-text="controlStatusText"
        :duration-text="durationText"
        cancel-label="重录"
        confirm-label="发送"
        :confirm-disabled="!reviewTranscriptText.trim()"
        @toggle="toggleRecording"
        @cancel="cancelRecording"
        @confirm="submitReview"
        @write="openTextInput"
      />
    </template>
    <template #footer>
      <text v-if="errorMsg" class="voice-page__error">{{ errorMsg }}</text>
      <ChatDailyLimitModal v-if="dailyLimitModalVisible" @confirm="handleDailyLimitConfirm" />
    </template>
  </ChatCabinScene>
</template>

<style scoped lang="scss">
.voice-page__error {
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

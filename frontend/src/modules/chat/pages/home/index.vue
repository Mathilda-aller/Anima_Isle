<script setup lang="ts">
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { CHAT_ASSETS } from "@/modules/chat/assets";
import { useChatStore } from "@/modules/chat/store/chat";
import { ROUTES } from "@/shared/constants/routes";
import { toLogin } from "@/shared/utils/navigation";
import { ApiError } from "@/shared/types/http";
import HomeNavItem from "@/modules/chat/components/HomeNavItem.vue";
import HomeInputButton from "@/modules/chat/components/HomeInputButton.vue";
import VoiceInputButton from "@/modules/chat/components/VoiceInputButton.vue";
import NightIp from "@/shared/components/NightIp.vue";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { getStyleOnboardingCompleted } from "@/infrastructure/storage/auth";

const authStore = useAuthStore();
const chatStore = useChatStore();
const errorMsg = ref("");

onShow(() => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }
  if (!getStyleOnboardingCompleted()) {
    uni.reLaunch({ url: ROUTES.STYLE_PICKER });
  }
});

function normalizeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    return JSON.stringify(error.detail);
  }
  return "请求失败，请稍后重试";
}

function openComposer() {
  chatStore.resetSession();
  uni.navigateTo({ url: `${ROUTES.CHAT_CABIN}?fresh=1` });
}

async function onConfirmTicket() {
  errorMsg.value = "";
  try {
    await chatStore.confirmTicketSelection();
    uni.showToast({ title: "已收下船票", icon: "success" });
  } catch (error) {
    errorMsg.value = normalizeError(error);
  }
}

function chooseCandidate(imageUrl: string) {
  chatStore.chooseCandidate(imageUrl);
}

function openVoiceInput() {
  chatStore.resetSession();
  uni.navigateTo({ url: `${ROUTES.CHAT_VOICE}?fresh=1` });
}

function goMemoryLane() {
  uni.navigateTo({ url: ROUTES.TICKET_LIST });
}

function goResident() {
  uni.navigateTo({ url: ROUTES.AUTH_RESIDENT });
}

function goSquare() {
  uni.navigateTo({ url: ROUTES.SQUARE_MAP });
}

function goPublish() {
  if (!chatStore.ticketDraft) return;
  uni.navigateTo({
    url: `${ROUTES.SQUARE_PUBLISH}?ticket_uid=${encodeURIComponent(chatStore.ticketDraft.ticket_uid)}`,
  });
}
</script>

<template>
  <StageViewportShell>
    <view class="home-inner">
      <view class="greeting">
        <text class="hello">晚上好，欢迎来到言屿</text>
        <text class="en">GOOD NIGHT</text>
      </view>

      <view class="ip-stage">
        <image class="ip-frame" :src="CHAT_ASSETS.icons.ipEllipseGlow" mode="aspectFit" />
        <view class="ip-halo"></view>
        <NightIp class="ip-character" />
        <view class="ip-nav">
          <view class="nav-orbit nav-left" hover-class="tap-hover" @click="goMemoryLane">
            <HomeNavItem label="记忆航线" :icon="CHAT_ASSETS.icons.navMemory" />
          </view>
          <view class="nav-orbit nav-center" hover-class="tap-hover" @click="goResident">
            <HomeNavItem label="成为屿民" :icon="CHAT_ASSETS.icons.navResident" />
          </view>
          <view class="nav-orbit nav-right" hover-class="tap-hover" @click="goSquare">
            <HomeNavItem label="共感群岛" :icon="CHAT_ASSETS.icons.navSquare" />
          </view>
        </view>
      </view>

      <view class="prompt">
        <text class="cn">此刻，你想把什么托付给这片海？</text>
        <text class="en">TRUST YOUR THOUGHTS TO THE OCEAN</text>
      </view>

      <view class="input-actions">
        <view class="action-trigger" hover-class="tap-hover" @click="openVoiceInput">
          <VoiceInputButton
            :glow-image="CHAT_ASSETS.images.inputGlow"
            :mic-body="CHAT_ASSETS.icons.voiceBody"
            label="语音输入"
          />
        </view>
        <view class="action-trigger" hover-class="tap-hover" @click="openComposer">
          <HomeInputButton
            label="文字输入"
            :icon="CHAT_ASSETS.icons.writeEntry"
            :glow-image="CHAT_ASSETS.images.inputGlow"
          />
        </view>
      </view>

      <view v-if="chatStore.ticketDraft" class="ticket-result">
        <image class="ticket-image" :src="chatStore.ticketDraft.image_url" mode="aspectFill" />
        <text class="ticket-poem">{{ chatStore.ticketDraft.poem_content }}</text>
        <view class="candidate-grid">
          <view
            v-for="item in chatStore.ticketDraft.candidate_images"
            :key="item.image_url"
            class="candidate"
            hover-class="tap-hover"
            @click="chooseCandidate(item.image_url)"
          >
            <image :src="item.image_url" mode="aspectFill" />
          </view>
        </view>
        <view class="ticket-actions">
          <button class="small-btn" hover-class="button-hover" @click="onConfirmTicket">收下船票</button>
          <button class="small-btn ghost" hover-class="button-hover" @click="goPublish">发送到岛屿</button>
        </view>
      </view>

      <text v-if="errorMsg" class="error">{{ errorMsg }}</text>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.home-inner {
  position: relative;
  min-height: 100vh;
  padding: 0 24rpx calc(24rpx + env(safe-area-inset-bottom));
  padding-top: calc(88rpx + env(safe-area-inset-top));
  box-sizing: border-box;
}

.greeting {
  position: relative;
  width: 76.5%;
  max-width: 615rpx;
  margin: 0 auto;
  text-align: center;
  z-index: 2;
}

.hello {
  color: var(--anima-text-strong);
  font-size: 44rpx;
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
}

.greeting .en {
  margin-top: 8rpx;
  display: block;
  color: var(--anima-text-muted);
  opacity: 0.95;
  letter-spacing: 4rpx;
  font-size: 30rpx;
  font-family: var(--anima-font-display);
}

.ip-stage {
  position: relative;
  width: 82.59%;
  max-width: 664rpx;
  margin: 16rpx auto 0;
  aspect-ratio: 332 / 409;
  z-index: 2;
}

.ip-frame {
  position: absolute;
  left: -9.34%;
  top: -14.43%;
  width: 117.47%;
  height: 95.35%;
  opacity: 1;
  z-index: 1;
}

.ip-halo {
  position: absolute;
  left: 11.45%;
  top: 7.82%;
  width: 81.93%;
  height: 66.5%;
  border-radius: 50%;
  background: radial-gradient(circle at 50% 50%, #74d4ea 0%, #5aa6b7 12.74%, rgba(65, 120, 132, 0) 25.481%);
  filter: blur(64rpx);
  opacity: 0.95;
  z-index: 2;
}

.ip-character {
  position: absolute;
  left: 5.42%;
  top: 14.43%;
  width: 89.21%;
  z-index: 3;
}

.ip-nav {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 4;
}

.nav-orbit {
  position: absolute;
  width: 15.06%;
  pointer-events: auto;
  transition: opacity 0.2s ease, transform 0.2s ease;
  font-size: 21rpx;
}

.nav-left {
  left: 2.71%;
  top: 60.39%;
}

.nav-center {
  left: 49.4%;
  top: 75.79%;
  transform: translateX(-50%);
}

.nav-right {
  left: 82.08%;
  top: 61.86%;
}

.prompt {
  position: relative;
  z-index: 2;
  margin-top: 24rpx;
  width: 76.37%;
  max-width: 614rpx;
  margin-left: auto;
  margin-right: auto;
  text-align: center;
}

.prompt .cn {
  color: var(--anima-text-main);
  font-size: 44rpx;
  text-shadow: var(--anima-shadow-title);
  white-space: normal;
  line-height: 1.3;
  font-family: var(--anima-font-display);
}

.prompt .en {
  margin-top: 14rpx;
  display: block;
  font-size: 30rpx;
  color: var(--anima-text-soft);
  letter-spacing: 3rpx;
  line-height: 1.25;
  font-family: var(--anima-font-display);
}

.input-actions {
  position: relative;
  z-index: 2;
  margin: 112rpx auto 0;
  width: 75.62%;
  max-width: 608rpx;
  display: flex;
  justify-content: space-between;
}

.input-actions > .action-trigger {
  width: 29.36%;
}

.action-trigger {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.ticket-result {
  position: relative;
  margin: 24rpx;
  padding: 18rpx;
  border-radius: var(--anima-radius-lg);
  background: var(--anima-surface-card);
  z-index: 3;
}

.ticket-image {
  width: 100%;
  height: 300rpx;
  border-radius: var(--anima-radius-sm);
}

.ticket-poem {
  margin-top: 10rpx;
  display: block;
  color: var(--text-primary);
  white-space: pre-wrap;
  font-family: var(--anima-font-display);
}

.candidate-grid {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
}

.candidate {
  height: 120rpx;
}

.candidate image {
  width: 100%;
  height: 100%;
  border-radius: var(--anima-radius-sm);
}

.ticket-actions {
  margin-top: 12rpx;
  display: flex;
  gap: 10rpx;
}

.small-btn {
  flex: 1;
  border: none;
  border-radius: var(--anima-radius-sm);
  background: var(--anima-button-primary);
  color: var(--text-primary);
}

.small-btn.ghost {
  background: var(--anima-button-secondary);
}

.error {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: 12rpx;
  z-index: 20;
  text-align: center;
  color: var(--anima-text-error);
}

.tap-hover {
  opacity: 0.82;
  transform: translateY(-4rpx);
}

.button-hover {
  opacity: 0.88;
}

@media (min-width: 900px) {
  .home-inner {
    padding-top: 64rpx;
  }
}
</style>

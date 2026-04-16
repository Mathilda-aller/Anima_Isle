<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import TicketShareGlyph from "@/modules/ticket/components/TicketShareGlyph.vue";
import { TICKET_ASSETS } from "@/modules/ticket/assets";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { ROUTES } from "@/shared/constants/routes";
import { toLogin } from "@/shared/utils/navigation";
import { SHARED_ASSETS } from "@/shared/assets";
import { ApiError } from "@/shared/types/http";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { logEvent } from "@/infrastructure/http/tracking";

const authStore = useAuthStore();
const ticketStore = useTicketStore();
const ticketUid = ref("");
const loading = ref(false);
const errorMsg = ref("");
const imageLoadFailed = ref(false);

const ticketDetail = computed(() => {
  if (!ticketUid.value) return null;
  return ticketStore.detailMap[ticketUid.value] ?? null;
});

const poemLines = computed(() => {
  const lines = (ticketDetail.value?.poem_content ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.length ? lines.slice(0, 3) : ["海风替你留住", "这一刻的心声", "也照亮回航的路"];
});

const createdAtLabel = computed(() => {
  const createdAt = ticketDetail.value?.created_at;
  if (!createdAt) return "";

  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return "";

  const chineseDigits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  const yearText = String(date.getFullYear())
    .split("")
    .map((digit) => chineseDigits[Number(digit)] ?? digit)
    .join("");

  const month = date.getMonth() + 1;
  const season =
    month >= 3 && month <= 5
      ? "春"
      : month >= 6 && month <= 8
        ? "夏"
        : month >= 9 && month <= 11
          ? "秋"
          : "冬";

  return `${yearText}年·${season}`;
});

function normalizeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    return JSON.stringify(error.detail);
  }
  return "船票靠岸时遇到了一点问题，请稍后再试";
}

onLoad(async (query) => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  ticketUid.value = (query?.ticket_uid as string) || "";
  if (!ticketUid.value) return;

  loading.value = true;
  errorMsg.value = "";
  try {
    await ticketStore.fetchDetail(ticketUid.value);
    imageLoadFailed.value = false;
  } catch (error) {
    errorMsg.value = normalizeError(error);
  } finally {
    loading.value = false;
  }
});

function handleImageLoad() {
  imageLoadFailed.value = false;
}

function handleImageError() {
  imageLoadFailed.value = true;
  const currentUrl = ticketDetail.value?.image_url || "";
  console.error("[ticket-detail] image load failed", {
    ticket_uid: ticketUid.value,
    image_url: currentUrl,
  });
  void logEvent("ticket_image_load_failed", {
    page: "ticket_detail",
    ticket_uid: ticketUid.value,
    image_url: currentUrl,
  });
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  uni.switchTab?.({ url: ROUTES.CHAT_HOME });
  uni.reLaunch({ url: ROUTES.CHAT_HOME });
}

function shareTicket() {
  uni.showToast({ title: "分享功能即将开放", icon: "none" });
}

function openViewer() {
  if (!ticketUid.value) return;
  uni.navigateTo({
    url: `${ROUTES.TICKET_VIEWER}?ticket_uid=${encodeURIComponent(ticketUid.value)}`,
  });
}

function goPublish() {
  if (!ticketUid.value) return;
  uni.navigateTo({
    url: `${ROUTES.SQUARE_PUBLISH}?ticket_uid=${encodeURIComponent(ticketUid.value)}`,
  });
}

function keepPrivate() {
  uni.showToast({ title: "已为你独自收藏", icon: "success" });
  uni.navigateTo({ url: ROUTES.TICKET_LIST });
}
</script>

<template>
  <StageViewportShell>
    <view class="ticket-detail-page__inner">
      <view v-if="loading" class="ticket-detail-page__state">
        <text class="ticket-detail-page__state-text">船票靠岸中...</text>
      </view>

      <view v-else-if="ticketDetail" class="ticket-detail-page__artboard">
        <view class="ticket-detail-page__topbar">
          <view class="ticket-detail-page__back" hover-class="tap-hover" @click="goBack">
            <image class="ticket-detail-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
          </view>
          <text class="ticket-detail-page__date">{{ createdAtLabel }}</text>
          <view class="ticket-detail-page__share" hover-class="tap-hover" @click="shareTicket">
            <TicketShareGlyph class="ticket-detail-page__share-icon" />
          </view>
        </view>

        <view class="ticket-detail-page__cover-shell" hover-class="tap-hover" @click="openViewer">
          <view class="ticket-detail-page__halo" />
          <view class="ticket-detail-page__aura" />
          <view class="ticket-detail-page__cover">
            <image
              class="ticket-detail-page__image"
              :src="ticketDetail.image_url"
              mode="scaleToFill"
              @load="handleImageLoad"
              @error="handleImageError"
            />
          </view>
          <text v-if="imageLoadFailed" class="ticket-detail-page__image-error">
            这张图暂时没有成功加载，请检查当前船票的图片链接。
          </text>
        </view>

        <view class="ticket-detail-page__poem">
          <text
            v-for="(line, index) in poemLines"
            :key="`${index}-${line}`"
            class="ticket-detail-page__poem-line"
            :class="{ 'ticket-detail-page__poem-line--last': index === poemLines.length - 1 }"
          >
            {{ line }}
          </text>
        </view>

        <view class="ticket-detail-page__actions">
          <view class="ticket-detail-page__action" hover-class="ticket-detail-page__action--hover" @click="goPublish">
            <image class="ticket-detail-page__action-icon" :src="TICKET_ASSETS.icons.publish" mode="aspectFit" />
            <text class="ticket-detail-page__action-label">寄至群岛</text>
          </view>

          <view class="ticket-detail-page__action" hover-class="ticket-detail-page__action--hover" @click="keepPrivate">
            <image class="ticket-detail-page__action-icon" :src="TICKET_ASSETS.icons.collect" mode="aspectFit" />
            <text class="ticket-detail-page__action-label">独自收藏</text>
          </view>
        </view>
      </view>

      <view v-else class="ticket-detail-page__state">
        <text class="ticket-detail-page__state-text">{{ errorMsg || "暂时还没有找到这张船票" }}</text>
      </view>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.ticket-detail-page__inner {
  position: relative;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1;
}

.ticket-detail-page__artboard {
  position: relative;
  width: min(100%, calc((100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) * 402 / 874));
  max-width: 804rpx;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  aspect-ratio: 402 / 874;
}

.ticket-detail-page__state {
  width: 100%;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}

.ticket-detail-page__state-text {
  color: $anima-text-dim;
  font-family: $anima-font-display;
  font-size: 28rpx;
  text-align: center;
}

.ticket-detail-page__topbar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: calc(44rpx + env(safe-area-inset-top)) 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 4;
}

.ticket-detail-page__back,
.ticket-detail-page__share {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 180ms ease, transform 180ms ease;
}

.ticket-detail-page__back-icon,
.ticket-detail-page__share-icon {
  width: 48rpx;
  height: 48rpx;
}

.ticket-detail-page__cover-shell {
  transition: opacity 180ms ease, transform 180ms ease;
}

.ticket-detail-page__image-error {
  position: absolute;
  left: 12%;
  right: 12%;
  top: 82%;
  color: $anima-text-error;
  font-family: $anima-font-display;
  font-size: 22rpx;
  line-height: 1.6;
  text-align: center;
  z-index: 4;
}

.ticket-detail-page__date {
  color: $anima-text-muted;
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 58rpx;
  letter-spacing: 1rpx;
  text-align: center;
}

.ticket-detail-page__cover-shell {
  position: absolute;
  left: 9.95%;
  top: 15.45%;
  width: 80.6%;
  height: 52.63%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ticket-detail-page__halo {
  position: absolute;
  left: 50%;
  top: 35%;
  width: 544rpx;
  height: 544rpx;
  border-radius: 50%;
  background: $anima-glow-ticket;
  filter: blur(128rpx);
  mix-blend-mode: screen;
  opacity: 0.92;
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.ticket-detail-page__aura {
  position: absolute;
  inset: 4% 8% 36%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(116, 212, 234, 0.9) 0%, rgba(90, 166, 183, 0.42) 28%, rgba(65, 120, 132, 0) 72%);
  filter: blur(64rpx);
  opacity: 0.95;
}

.ticket-detail-page__cover {
  position: relative;
  width: 100%;
  height: 100%;
  box-shadow: 8rpx 8rpx 48rpx rgba(0, 0, 0, 0.25);
}

.ticket-detail-page__image {
  width: 100%;
  height: 100%;
}

.ticket-detail-page__poem {
  position: absolute;
  left: 14%;
  top: 70.5%;
  width: 72%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  text-align: center;
}

.ticket-detail-page__poem-line {
  color: #fff;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.37);
}

.ticket-detail-page__poem-line--last {
  font-size: 40rpx;
}

.ticket-detail-page__actions {
  position: absolute;
  left: 15.17%;
  top: 89.25%;
  width: 69.65%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ticket-detail-page__action {
  width: 198rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.6);
  border-radius: 32rpx;
  background:
    linear-gradient(90deg, rgba(21, 31, 53, 0.75) 0%, rgba(50, 71, 128, 0.12) 52%, rgba(21, 31, 53, 0.75) 100%);
  box-shadow: inset 0 0 20rpx rgba(255, 255, 255, 0.1);
  transition: opacity 180ms ease, transform 180ms ease;
}

.ticket-detail-page__action-icon {
  width: 32rpx;
  height: 32rpx;
}

.ticket-detail-page__action-label {
  color: $anima-text-main;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.ticket-detail-page__action--hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}

.tap-hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}

@media screen and (max-width: 360px) {
  .ticket-detail-page__actions {
    left: 12%;
    width: 76%;
  }

  .ticket-detail-page__action {
    width: 210rpx;
  }

  .ticket-detail-page__action-label {
    font-size: 28rpx;
  }
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import TicketCloseGlyph from "@/modules/ticket/components/TicketCloseGlyph.vue";
import TicketShareGlyph from "@/modules/ticket/components/TicketShareGlyph.vue";
import { TICKET_ASSETS } from "@/modules/ticket/assets";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { ROUTES } from "@/shared/constants/routes";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { toLogin } from "@/shared/utils/navigation";
import { logEvent } from "@/infrastructure/http/tracking";
import {
  formatTicketMetaTime,
  formatTicketMonthDay,
  formatTicketSeasonLabel,
  formatTicketWeekday,
} from "@/modules/ticket/utils/ticketDate";

const authStore = useAuthStore();
const ticketStore = useTicketStore();
const ticketUid = ref("");
const loading = ref(false);
const showingBack = ref(false);
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

const diaryText = computed(() => {
  const content = ticketDetail.value?.user_diary_summary?.trim();
  if (content) return content;
  return "今天的身体和思绪都很沉重，我看见了自己的疲惫，也允许它存在。即便什么都不做，我也知道自己停留在这里，这一刻的安静本身就是一种力量。";
});

const createdAtLabel = computed(() => {
  return formatTicketSeasonLabel(ticketDetail.value?.created_at);
});

const diaryMonthDay = computed(() => {
  return formatTicketMonthDay(ticketDetail.value?.created_at);
});

const diaryWeekday = computed(() => {
  return formatTicketWeekday(ticketDetail.value?.created_at);
});

const diaryMetaTime = computed(() => {
  return formatTicketMetaTime(ticketDetail.value?.created_at);
});

onLoad(async (query) => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  ticketUid.value = (query?.ticket_uid as string) || "";
  showingBack.value = query?.side === "back";
  if (!ticketUid.value) return;

  loading.value = true;
  try {
    await ticketStore.fetchDetail(ticketUid.value);
    imageLoadFailed.value = false;
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
  console.error("[ticket-viewer] image load failed", {
    ticket_uid: ticketUid.value,
    image_url: currentUrl,
  });
  void logEvent("ticket_image_load_failed", {
    page: "ticket_viewer",
    ticket_uid: ticketUid.value,
    image_url: currentUrl,
  });
}

function closeViewer() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  const detailUrl = ticketUid.value
    ? `${ROUTES.TICKET_DETAIL}?ticket_uid=${encodeURIComponent(ticketUid.value)}`
    : ROUTES.TICKET_DETAIL;
  uni.reLaunch({ url: detailUrl });
}

function shareTicket() {
  uni.showToast({ title: "分享功能即将开放", icon: "none" });
}

function toggleCard() {
  if (!ticketDetail.value) return;
  showingBack.value = !showingBack.value;
}
</script>

<template>
  <StageViewportShell>
    <view class="ticket-viewer" @click="toggleCard">
      <view v-if="ticketDetail" class="ticket-viewer__artboard">
        <template v-if="!showingBack">
          <image
            class="ticket-viewer__image"
            :src="ticketDetail.image_url"
            mode="aspectFill"
            @load="handleImageLoad"
            @error="handleImageError"
          />
          <view class="ticket-viewer__image-gradient" />
          <view v-if="imageLoadFailed" class="ticket-viewer__image-error-shell">
            <text class="ticket-viewer__image-error">这张图暂时没有成功加载。</text>
          </view>
        </template>
        <template v-else>
          <view class="ticket-viewer__backdrop" />
          <view class="ticket-viewer__back-card">
            <text class="ticket-viewer__weekday">{{ diaryWeekday }}</text>
            <text class="ticket-viewer__month-day">{{ diaryMonthDay }}</text>
            <scroll-view class="ticket-viewer__diary-scroll" scroll-y @click.stop>
              <text class="ticket-viewer__diary-body">{{ diaryText }}</text>
            </scroll-view>
            <image class="ticket-viewer__divider" :src="TICKET_ASSETS.icons.diaryDivider" mode="scaleToFill" />
            <view class="ticket-viewer__meta">
              <view class="ticket-viewer__meta-tag">
                <view class="ticket-viewer__meta-dot">
                  <image class="ticket-viewer__meta-dot-outer" :src="TICKET_ASSETS.icons.diaryDotOuter" mode="aspectFit" />
                  <image class="ticket-viewer__meta-dot-inner" :src="TICKET_ASSETS.icons.diaryDotInner" mode="aspectFit" />
                </view>
                <text class="ticket-viewer__meta-text">{{ ticketDetail.island_category }}</text>
              </view>
              <text class="ticket-viewer__meta-text">{{ diaryMetaTime }}</text>
            </view>
          </view>
        </template>

        <view class="ticket-viewer__topbar">
          <view class="ticket-viewer__top-action" hover-class="tap-hover" @click.stop="closeViewer">
            <TicketCloseGlyph />
          </view>
          <text class="ticket-viewer__date">{{ createdAtLabel }}</text>
          <view class="ticket-viewer__top-action" hover-class="tap-hover" @click.stop="shareTicket">
            <TicketShareGlyph />
          </view>
        </view>

        <view class="ticket-viewer__poem">
          <text
            v-for="(line, index) in poemLines"
            :key="`${index}-${line}`"
            class="ticket-viewer__poem-line"
            :class="{ 'ticket-viewer__poem-line--last': index === poemLines.length - 1 }"
          >
            {{ line }}
          </text>
        </view>
      </view>

      <view v-else class="ticket-viewer__state">
        <text class="ticket-viewer__state-text">{{ loading ? "船票靠岸中..." : "暂时还没有找到这张船票" }}</text>
      </view>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.ticket-viewer {
  position: relative;
  min-height: 100vh;
}

.ticket-viewer__artboard {
  position: relative;
  width: 100%;
  min-height: 100vh;
}

.ticket-viewer__image,
.ticket-viewer__backdrop {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.ticket-viewer__image-error-shell {
  position: absolute;
  left: 50%;
  bottom: 160rpx;
  transform: translateX(-50%);
  z-index: 3;
  padding: 18rpx 28rpx;
  border-radius: 999rpx;
  background: rgba(16, 28, 42, 0.56);
  backdrop-filter: blur(10rpx);
}

.ticket-viewer__image-error {
  color: #fff;
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
}

.ticket-viewer__backdrop {
  background:
    radial-gradient(circle at 78% 16%, rgba(116, 212, 234, 0.4) 0%, rgba(65, 120, 132, 0) 28%),
    linear-gradient(180deg, #072743 0%, #2c417a 49.52%, #3f4376 100%);
}

.ticket-viewer__image-gradient {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 46.34%;
  background: linear-gradient(180deg, rgba(108, 130, 225, 0) 0%, rgba(78, 94, 162, 0.62) 59.135%, #3b477b 100%);
}

.ticket-viewer__topbar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  box-sizing: border-box;
  padding: calc(44rpx + env(safe-area-inset-top)) 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 4;
}

.ticket-viewer__top-action {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ticket-viewer__date {
  color: rgba(209, 213, 220, 0.92);
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 58rpx;
  letter-spacing: 1rpx;
  text-align: center;
}

.ticket-viewer__poem {
  position: absolute;
  left: 14%;
  bottom: 10.18%;
  width: 72%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  text-align: center;
  z-index: 3;
}

.ticket-viewer__poem-line {
  color: #fff;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.37);
}

.ticket-viewer__poem-line--last {
  font-size: 40rpx;
}

.ticket-viewer__back-card {
  position: absolute;
  left: 9.7%;
  top: 14.76%;
  width: 80.6%;
  height: 52.63%;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 66rpx 38rpx 40rpx;
  border-radius: 42rpx;
  background:
    radial-gradient(circle at 100% 0%, rgba(18, 211, 255, 0.19) 0%, rgba(128, 231, 254, 0.1) 40%, rgba(255, 255, 255, 0) 100%),
    linear-gradient(180deg, rgba(61, 88, 157, 0.72) 0%, rgba(57, 72, 135, 0.7) 100%);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 40rpx rgba(255, 255, 255, 0.08);
  z-index: 2;
}

.ticket-viewer__weekday {
  color: rgba(209, 213, 220, 0.9);
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 35rpx;
  letter-spacing: 3rpx;
  text-transform: uppercase;
}

.ticket-viewer__month-day {
  margin-top: 12rpx;
  display: block;
  color: #fff;
  font-family: $anima-font-display;
  font-size: 52rpx;
  line-height: 1.1;
  letter-spacing: 1rpx;
}

.ticket-viewer__diary-scroll {
  margin-top: 74rpx;
  flex: 1;
  min-height: 0;
}

.ticket-viewer__diary-body {
  display: block;
  color: rgba(255, 255, 255, 0.86);
  font-family: $anima-font-display;
  font-size: 34rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  white-space: pre-wrap;
  word-break: break-word;
}

.ticket-viewer__divider {
  margin-top: 54rpx;
  width: 100%;
  height: 2rpx;
  opacity: 0.7;
}

.ticket-viewer__meta {
  margin-top: 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.ticket-viewer__meta-tag {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.ticket-viewer__meta-dot {
  position: relative;
  width: 18rpx;
  height: 18rpx;
}

.ticket-viewer__meta-dot-outer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.ticket-viewer__meta-dot-inner {
  position: absolute;
  left: 4rpx;
  top: 4rpx;
  width: 10rpx;
  height: 10rpx;
}

.ticket-viewer__meta-text {
  color: rgba(209, 213, 220, 0.92);
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 35rpx;
  letter-spacing: 1rpx;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ticket-viewer__state {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}

.ticket-viewer__state-text {
  color: $anima-text-dim;
  font-family: $anima-font-display;
  font-size: 28rpx;
  text-align: center;
}

.tap-hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}
</style>

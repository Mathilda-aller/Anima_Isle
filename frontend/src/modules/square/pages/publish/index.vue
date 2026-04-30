<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { CHAT_ASSETS } from "@/modules/chat/assets";
import { getIslandIdByBackendKey } from "@/modules/square/constants/islands";
import { useSquareStore } from "@/modules/square/store/square";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { TICKET_ASSETS } from "@/modules/ticket/assets";
import { SHARED_ASSETS } from "@/shared/assets";
import { ROUTES } from "@/shared/constants/routes";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { toLogin } from "@/shared/utils/navigation";

interface BubbleLayout {
  id: string;
  tag: string;
  size: number;
  left: number;
  top: number;
  fontSize: number;
}

const authStore = useAuthStore();
const squareStore = useSquareStore();
const ticketStore = useTicketStore();
const ticketUid = ref("");
const loading = ref(false);

const ticketDetail = computed(() => {
  if (!ticketUid.value) return null;
  return ticketStore.detailMap[ticketUid.value] ?? null;
});

const bubbleLayouts = ref<BubbleLayout[]>([]);
const displayedTags = computed(() => {
  const normalized = squareStore.suggestedTags.length
    ? squareStore.suggestedTags.map((tag) => (tag.startsWith("#") ? tag : `#${tag}`))
    : ["#心情"];

  const result: string[] = [];
  while (result.length < 5) {
    const next = normalized[result.length % normalized.length];
    result.push(next);
  }
  return result.slice(0, 5);
});

function sampleBetween(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function shuffle<T>(items: T[]) {
  const cloned = [...items];
  for (let index = cloned.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [cloned[index], cloned[swapIndex]] = [cloned[swapIndex], cloned[index]];
  }
  return cloned;
}

function buildBubbleLayouts(tags: string[]) {
  const sizeRanges: Array<[number, number]> = [
    [108, 120],
    [122, 136],
    [138, 152],
    [154, 168],
    [172, 186],
  ];
  const shuffledSizes = shuffle(sizeRanges).map(([min, max]) => Math.round(sampleBetween(min, max)));
  const placements: BubbleLayout[] = [];

  tags.forEach((tag, index) => {
    const size = shuffledSizes[index] ?? 132;
    const radiusX = (size / 620) * 52;
    const radiusY = (size / 430) * 52;

    let left = 50;
    let top = 50;
    let placed = false;

    for (let attempt = 0; attempt < 60; attempt += 1) {
      const nextLeft = sampleBetween(12, 88);
      const nextTop = sampleBetween(14, 84);
      const overlaps = placements.some((item) => {
        const dx = Math.abs(item.left - nextLeft);
        const dy = Math.abs(item.top - nextTop);
        const minDx = radiusX + (item.size / 620) * 30;
        const minDy = radiusY + (item.size / 430) * 30;
        return dx < minDx && dy < minDy;
      });

      if (!overlaps) {
        left = nextLeft;
        top = nextTop;
        placed = true;
        break;
      }
    }

    if (!placed && placements.length) {
      const anchor = placements[index % placements.length];
      left = Math.min(84, Math.max(16, anchor.left + sampleBetween(-18, 18)));
      top = Math.min(82, Math.max(16, anchor.top + sampleBetween(-16, 16)));
    }

    placements.push({
      id: `${tag}-${index}`,
      tag,
      size,
      left,
      top,
      fontSize: size >= 170 ? 24 : size >= 145 ? 22 : 20,
    });
  });

  bubbleLayouts.value = placements;
}

async function loadPageData(forceRefreshTags = false) {
  if (!ticketUid.value) return;

  loading.value = true;
  try {
    await Promise.all([
      ticketStore.fetchDetail(ticketUid.value),
      squareStore.suggestTagsForTicket(ticketUid.value, { force: forceRefreshTags }),
    ]);
    buildBubbleLayouts(displayedTags.value);
  } finally {
    loading.value = false;
  }
}

onLoad(async (query) => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  ticketUid.value = (query?.ticket_uid as string) || "";
  if (!ticketUid.value) return;
  await loadPageData();
});

function toggle(tag: string) {
  squareStore.toggleTag(tag);
}

async function regenerateTags() {
  if (!ticketUid.value || loading.value) return;
  await loadPageData(true);
}

async function doPublish() {
  if (!ticketUid.value || loading.value) return;
  if (!squareStore.selectedTags.length) {
    uni.showToast({ title: "请至少选择一个tag", icon: "none" });
    return;
  }

  loading.value = true;
  try {
    const publishedTicket = await squareStore.publish(ticketUid.value);
    const islandId = getIslandIdByBackendKey(publishedTicket.island_category);
    uni.showToast({ title: "已发送到岛屿", icon: "success" });
    uni.redirectTo({
      url: `${ROUTES.SQUARE_ISLAND}?island_id=${encodeURIComponent(islandId)}&ticket_uid=${encodeURIComponent(ticketUid.value)}&entry=publish`,
    });
  } finally {
    loading.value = false;
  }
}

function goBack() {
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
</script>

<template>
  <StageViewportShell>
    <view class="publish-page__inner">
      <view v-if="loading && !ticketDetail" class="publish-page__state">
        <text class="publish-page__state-text">言屿正在整理共鸣标签...</text>
      </view>

      <view v-else-if="ticketDetail" class="publish-page__artboard">
        <view class="publish-page__topbar">
          <view class="publish-page__back" hover-class="tap-hover" @click="goBack">
            <image class="publish-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
          </view>
        </view>

        <text class="publish-page__title">选择一个共鸣tag，让更多人看见你的情绪</text>

        <view class="publish-page__cover-shell">
          <view class="publish-page__cover-aura" />
          <view class="publish-page__cover">
            <image class="publish-page__cover-image" :src="ticketDetail.image_url" mode="aspectFill" />
          </view>
        </view>

        <view class="publish-page__bubble-field">
          <view
            v-for="bubble in bubbleLayouts"
            :key="bubble.id"
            class="publish-page__bubble"
            :class="{ 'publish-page__bubble--selected': squareStore.selectedTags.includes(bubble.tag) }"
            :style="{
              width: `${bubble.size}rpx`,
              height: `${bubble.size}rpx`,
              left: `${bubble.left}%`,
              top: `${bubble.top}%`,
            }"
            hover-class="publish-page__bubble--hover"
            @click="toggle(bubble.tag)"
          >
            <text class="publish-page__bubble-label" :style="{ fontSize: `${bubble.fontSize}rpx` }">
              {{ bubble.tag }}
            </text>
          </view>
        </view>

        <view class="publish-page__actions">
          <view
            class="publish-page__publish-action"
            :class="{ 'publish-page__publish-action--disabled': loading }"
            hover-class="publish-page__action-hover"
            @click="doPublish"
          >
            <image class="publish-page__publish-icon" :src="TICKET_ASSETS.icons.publish" mode="aspectFit" />
            <text class="publish-page__publish-label">{{ loading ? "寄送中" : "寄至群岛" }}</text>
          </view>

          <view
            class="publish-page__reroll"
            :class="{ 'publish-page__reroll--disabled': loading }"
            hover-class="publish-page__reroll--hover"
            @click="regenerateTags"
          >
            <image class="publish-page__reroll-icon" :src="CHAT_ASSETS.icons.ticketRerollRefresh" mode="aspectFit" />
            <text class="publish-page__reroll-text">重新生成</text>
          </view>
        </view>
      </view>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
$publish-title-top: 15.1%;
$publish-cover-top: 22.6%;
$publish-actions-top: 87.25%;
$publish-action-gap: 40rpx;

.publish-page__inner {
  position: relative;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1;
}

.publish-page__artboard {
  position: relative;
  width: min(100%, calc((100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) * 402 / 874));
  max-width: 804rpx;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  aspect-ratio: 402 / 874;
}

.publish-page__state {
  width: 100%;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}

.publish-page__state-text {
  color: $anima-text-dim;
  font-family: $anima-font-display;
  font-size: 28rpx;
  text-align: center;
}

.publish-page__topbar {
  position: absolute;
  top: 5.49%;
  left: 1%;
  width: 97.95%;
  padding: 0 4%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: calc(44rpx + env(safe-area-inset-top)) 32rpx 0;
  z-index: 4;
}

.publish-page__back {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 180ms ease, transform 180ms ease;
}

.publish-page__back-icon {
  width: 48rpx;
  height: 48rpx;
}

.publish-page__title {
  position: absolute;
  left: 12.2%;
  top: $publish-title-top;
  width: 79.4%;
  color: $anima-text-main;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  white-space: nowrap;
  word-break: keep-all;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.publish-page__cover-shell {
  position: absolute;
  left: 26.55%;
  top: $publish-cover-top;
  width: 47.41%;
  height: 30.32%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.publish-page__cover-aura {
  position: absolute;
  inset: -18% -12%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(116, 212, 234, 0.88) 0%, rgba(90, 166, 183, 0.4) 28%, rgba(65, 120, 132, 0) 72%);
  filter: blur(64rpx);
  opacity: 0.88;
}

.publish-page__cover {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 42rpx;
  box-shadow: 8rpx 8rpx 48rpx rgba(0, 0, 0, 0.25);
}

.publish-page__cover-image {
  width: 100%;
  height: 100%;
}

.publish-page__bubble-field {
  position: absolute;
  left: 6%;
  top: 54%;
  width: 88%;
  height: 28%;
}

.publish-page__bubble {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx;
  border-radius: 999rpx;
  background: radial-gradient(circle at 60% 38%, rgba(198, 244, 255, 0.78) 0%, rgba(141, 234, 255, 0.24) 48%, rgba(255, 255, 255, 0.2) 100%);
  box-shadow: 0 0 48rpx rgba(255, 255, 255, 0.25);
  transition: transform 180ms ease, opacity 180ms ease, box-shadow 180ms ease;
}

.publish-page__bubble--selected {
  background: radial-gradient(circle at 60% 38%, rgba(216, 249, 255, 0.95) 0%, rgba(165, 236, 255, 0.56) 55%, rgba(255, 255, 255, 0.42) 100%);
  box-shadow: 0 0 60rpx rgba(192, 244, 255, 0.42);
}

.publish-page__bubble--hover {
  opacity: 0.9;
  transform: translate(-50%, -50%) scale(1.03);
}

.publish-page__bubble-label {
  max-width: 88%;
  color: #fff;
  font-family: $anima-font-display;
  line-height: 1.35;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.37);
}

.publish-page__actions {
  position: absolute;
  left: 50%;
  top: $publish-actions-top;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: $publish-action-gap;
}

.publish-page__publish-action {
  width: 198rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.6);
  border-radius: 30rpx;
  background:
    linear-gradient(90deg, rgba(21, 31, 53, 0.78) 0%, rgba(50, 71, 128, 0.12) 52%, rgba(21, 31, 53, 0.78) 100%);
  box-shadow: inset 0 0 20rpx rgba(255, 255, 255, 0.1);
  transition: opacity 180ms ease, transform 180ms ease;
}

.publish-page__publish-action--disabled,
.publish-page__reroll--disabled {
  opacity: $anima-button-disabled;
}

.publish-page__publish-icon {
  width: 32rpx;
  height: 32rpx;
}

.publish-page__publish-label {
  color: $anima-text-main;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.publish-page__reroll {
  width: 100rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  transition: opacity 180ms ease, transform 180ms ease;
}

.publish-page__reroll-icon {
  width: 46rpx;
  height: 46rpx;
}

.publish-page__reroll-text {
  color: $anima-text-dim;
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  white-space: nowrap;
  word-break: keep-all;
  writing-mode: horizontal-tb;
  text-align: center;
}

.publish-page__action-hover,
.publish-page__reroll--hover,
.tap-hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}
</style>

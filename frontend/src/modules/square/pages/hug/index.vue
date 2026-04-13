<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { SQUARE_ASSETS } from "@/modules/square/assets";
import { useSquareStore } from "@/modules/square/store/square";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { ROUTES } from "@/shared/constants/routes";
import { SHARED_ASSETS } from "@/shared/assets";
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";
import { toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const squareStore = useSquareStore();
const ticketStore = useTicketStore();
const ticketUid = ref("");
const islandId = ref("");
const tag = ref("");
const loading = ref(false);
const hugging = ref(false);
const hasHugged = ref(false);
const imageLoadFailed = ref(false);
const localHugOffset = ref(0);

const ticketDetail = computed(() => {
  if (!ticketUid.value) {
    return null;
  }

  return ticketStore.detailMap[ticketUid.value] ?? null;
});

const poemLines = computed(() => {
  const lines = (ticketDetail.value?.poem_content ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.length ? lines.slice(0, 3) : ["蝶翼载星入深海", "潮汐接住碎金芒", "光引归途不必慌"];
});

const createdAtLabel = computed(() => {
  const createdAt = ticketDetail.value?.created_at;
  if (!createdAt) {
    return "";
  }

  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

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

const hugCountLabel = computed(() => {
  const total = (ticketDetail.value?.hug_count ?? 0) + localHugOffset.value;
  return `${total}个拥抱`;
});

onLoad(async (query) => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  ticketUid.value = typeof query?.ticket_uid === "string" ? query.ticket_uid : "";
  islandId.value = typeof query?.island_id === "string" ? query.island_id : "";
  tag.value = typeof query?.tag === "string" ? query.tag : "";
  if (!ticketUid.value) {
    return;
  }

  loading.value = true;
  try {
    await ticketStore.fetchDetail(ticketUid.value);
    await squareStore.interact(ticketUid.value, "view");
  } finally {
    loading.value = false;
  }
});

function handleImageLoad() {
  imageLoadFailed.value = false;
}

function handleImageError() {
  imageLoadFailed.value = true;
}

function closePage() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  const fallbackUrl = islandId.value
    ? `${ROUTES.SQUARE_ISLAND}?island_id=${encodeURIComponent(islandId.value)}&entry=map`
    : ROUTES.SQUARE_MAP;
  uni.reLaunch({ url: fallbackUrl });
}

function openTicketViewer() {
  if (!ticketUid.value) {
    return;
  }

  uni.navigateTo({
    url: `${ROUTES.TICKET_VIEWER}?ticket_uid=${encodeURIComponent(ticketUid.value)}`,
  });
}

async function sendHug() {
  if (!ticketUid.value || hugging.value || hasHugged.value) {
    return;
  }

  hugging.value = true;
  try {
    await squareStore.interact(ticketUid.value, "hug");
    localHugOffset.value += 1;
    hasHugged.value = true;
  } finally {
    hugging.value = false;
  }
}
</script>

<template>
  <view class="square-hug-page">
    <DarkBackgroundLayer :texture-opacity="0.2" />
    <view class="square-hug-page__content">
      <view class="square-hug-page__topbar">
        <view class="square-hug-page__back" hover-class="tap-hover" @click="closePage">
          <image class="square-hug-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
        </view>
        <text class="square-hug-page__date">{{ createdAtLabel }}</text>
        <view class="square-hug-page__topbar-spacer"></view>
      </view>

      <template v-if="ticketDetail">
        <view class="square-hug-page__image-shell" hover-class="tap-hover" @click="openTicketViewer">
          <view class="square-hug-page__image-glow" />
          <image
            class="square-hug-page__image"
            :src="ticketDetail.image_url"
            mode="aspectFill"
            @load="handleImageLoad"
            @error="handleImageError"
          />
          <view v-if="imageLoadFailed" class="square-hug-page__image-fallback">
            <text class="square-hug-page__image-fallback-text">这张船票暂时没有成功加载</text>
          </view>
        </view>

        <view class="square-hug-page__poem">
          <text
            v-for="(line, index) in poemLines"
            :key="`${index}-${line}`"
            class="square-hug-page__poem-line"
            :class="{ 'square-hug-page__poem-line--emphasis': index === poemLines.length - 1 }"
          >
            {{ line }}
          </text>
        </view>

        <view class="square-hug-page__hug-meta">
          <image class="square-hug-page__hug-icon" :src="SQUARE_ASSETS.icons.hugHeart" mode="aspectFit" />
          <text class="square-hug-page__hug-count">{{ hugCountLabel }}</text>
        </view>

        <button
          class="square-hug-page__hug-button"
          :class="{ 'square-hug-page__hug-button--disabled': hugging || hasHugged }"
          :disabled="hugging || hasHugged"
          hover-class="square-hug-page__hug-button--hover"
          @click="sendHug"
        >
          {{ hasHugged ? "拥抱已送达" : "给ta一个拥抱" }}
        </button>
      </template>

      <view v-else class="square-hug-page__state">
        <text class="square-hug-page__state-text">
          {{ loading ? "正在靠近这张船票..." : "暂时还没有找到这张船票" }}
        </text>
        <text v-if="tag" class="square-hug-page__state-tag">{{ tag }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.square-hug-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--anima-night-gradient);
}

.square-hug-page__content {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  align-items: center;
  padding: 0 40rpx calc(54rpx + env(safe-area-inset-bottom));
}

.square-hug-page__topbar {
  position: relative;
  z-index: 2;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(44rpx + env(safe-area-inset-top)) 32rpx 0;
}

.square-hug-page__back,
.square-hug-page__topbar-spacer {
  display: flex;
  height: 48rpx;
  width: 48rpx;
  flex: 0 0 48rpx;
  align-items: center;
  justify-content: center;
}

.square-hug-page__back-icon {
  width: 48rpx;
  height: 48rpx;
}

.square-hug-page__date {
  color: var(--anima-text-muted);
  font-family: var(--anima-font-display);
  font-size: 24rpx;
  line-height: 58rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: var(--anima-shadow-title);
}

.square-hug-page__image-shell {
  position: relative;
  display: flex;
  width: 100%;
  max-width: 620rpx;
  margin-top: 92rpx;
  align-items: center;
  justify-content: center;
}

.square-hug-page__image-glow {
  position: absolute;
  top: 86rpx;
  left: 72rpx;
  width: 520rpx;
  height: 520rpx;
  border-radius: 999rpx;
  background: radial-gradient(circle, rgba(116, 212, 234, 0.42) 0%, rgba(65, 120, 132, 0.2) 52%, rgba(65, 120, 132, 0) 100%);
  filter: blur(64rpx);
  pointer-events: none;
}

.square-hug-page__image {
  position: relative;
  z-index: 1;
  width: 620rpx;
  height: 878rpx;
  border-radius: 40rpx;
  box-shadow: 8rpx 8rpx 48rpx rgba(0, 0, 0, 0.25);
}

.square-hug-page__image-fallback {
  position: absolute;
  z-index: 2;
  display: flex;
  width: 620rpx;
  height: 878rpx;
  align-items: center;
  justify-content: center;
  border-radius: 40rpx;
  background: rgba(16, 28, 42, 0.5);
  backdrop-filter: blur(12rpx);
}

.square-hug-page__image-fallback-text {
  color: rgba(255, 255, 255, 0.92);
  font-size: 26rpx;
  line-height: 42rpx;
  text-align: center;
}

.square-hug-page__poem {
  display: flex;
  width: 100%;
  margin-top: 42rpx;
  flex-direction: column;
  align-items: center;
}

.square-hug-page__poem-line {
  color: #ffffff;
  font-family: var(--anima-font-display);
  font-size: 32rpx;
  line-height: 68rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.37);
}

.square-hug-page__poem-line--emphasis {
  font-size: 40rpx;
}

.square-hug-page__hug-meta {
  display: flex;
  margin-top: 34rpx;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.square-hug-page__hug-icon {
  width: 44rpx;
  height: 44rpx;
}

.square-hug-page__hug-count {
  color: rgba(217, 217, 217, 0.81);
  font-family: var(--anima-font-display);
  font-size: 24rpx;
  line-height: 44rpx;
  text-align: center;
}

.square-hug-page__hug-button {
  display: flex;
  width: 210rpx;
  height: 64rpx;
  margin-top: 24rpx;
  align-items: center;
  justify-content: center;
  border: 1rpx solid rgba(255, 255, 255, 0.68);
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0);
  color: rgba(230, 248, 255, 0.96);
  font-family: var(--anima-font-display);
  font-size: 32rpx;
  line-height: 44rpx;
  white-space: nowrap;
}

.square-hug-page__hug-button::after {
  border: 0;
}

.square-hug-page__hug-button--hover,
.square-hug-page__hug-button--disabled {
  opacity: 0.72;
}

.square-hug-page__state {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.square-hug-page__state-text,
.square-hug-page__state-tag {
  color: rgba(255, 255, 255, 0.92);
  font-family: var(--anima-font-display);
  font-size: 28rpx;
  line-height: 42rpx;
  text-align: center;
}
</style>

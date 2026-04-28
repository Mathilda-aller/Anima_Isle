<script setup lang="ts">
import { ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    promptText?: string;
    imageUrl?: string;
    prefetchedImageUrl?: string;
    refreshIcon: string;
    acceptLabel?: string;
    acceptDisabled?: boolean;
    acceptLoading?: boolean;
    rerollDisabled?: boolean;
  }>(),
  {
    promptText: "这张卡片，是否触碰到了你的心声？",
    imageUrl: "",
    prefetchedImageUrl: "",
    acceptLabel: "收下",
    acceptDisabled: false,
    acceptLoading: false,
    rerollDisabled: false,
  },
);

const emit = defineEmits<{
  (e: "accept"): void;
  (e: "reroll"): void;
}>();

const imageState = ref<"idle" | "loading" | "ready" | "error">("idle");

watch(
  () => [props.imageUrl, props.prefetchedImageUrl] as const,
  ([nextImageUrl, prefetchedImageUrl]) => {
    if (!nextImageUrl) {
      imageState.value = "idle";
      return;
    }
    imageState.value = nextImageUrl === prefetchedImageUrl ? "ready" : "loading";
  },
  { immediate: true },
);

function onAccept() {
  if (props.acceptDisabled) return;
  emit("accept");
}

function onReroll() {
  if (props.rerollDisabled) return;
  emit("reroll");
}

function handleImageLoad() {
  imageState.value = "ready";
}

function handleImageError() {
  imageState.value = "error";
}
</script>

<template>
  <view class="chat-ticket-reveal-card">
    <text class="chat-ticket-reveal-card__prompt">{{ promptText }}</text>

    <view class="chat-ticket-reveal-card__card-shell">
      <view class="chat-ticket-reveal-card__card">
        <image
          v-if="imageUrl"
          :key="imageUrl"
          class="chat-ticket-reveal-card__image"
          :src="imageUrl"
          mode="aspectFill"
          :show-menu-by-longpress="false"
          @load="handleImageLoad"
          @error="handleImageError"
        />
        <view v-if="!imageUrl || imageState !== 'ready'" class="chat-ticket-reveal-card__placeholder">
          <text class="chat-ticket-reveal-card__placeholder-text">
            {{ imageState === "error" ? "图像暂未加载成功" : "图像整理中" }}
          </text>
        </view>
      </view>
    </view>

    <view
      class="chat-ticket-reveal-card__accept"
      :class="{
        'chat-ticket-reveal-card__accept--disabled': acceptDisabled,
      }"
      hover-class="chat-ticket-reveal-card__button--hover"
      @click="onAccept"
    >
      <text class="chat-ticket-reveal-card__accept-text">
        {{ acceptLoading ? "收下中" : acceptLabel }}
      </text>
    </view>

    <view
      class="chat-ticket-reveal-card__reroll"
      :class="{ 'chat-ticket-reveal-card__reroll--disabled': rerollDisabled }"
      hover-class="chat-ticket-reveal-card__button--hover"
      @click="onReroll"
    >
      <image class="chat-ticket-reveal-card__reroll-icon" :src="refreshIcon" mode="aspectFit" />
      <text class="chat-ticket-reveal-card__reroll-text">重新生成</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.chat-ticket-reveal-card {
  position: absolute;
  inset: 0;
  z-index: 3;
}

.chat-ticket-reveal-card__prompt {
  position: absolute;
  top: 15.9%;
  left: 18.6%;
  width: 79.4%;
  color: $anima-text-main;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.chat-ticket-reveal-card__card-shell {
  position: absolute;
  top: 23.2%;
  left: 21.9%;
  width: 58.6%;
  height: 38.6%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-ticket-reveal-card__card-shell::before {
  content: "";
  position: absolute;
  inset: -24rpx;
  border-radius: 80rpx;
  background: radial-gradient(circle, rgba(129, 224, 255, 0.8) 0%, rgba(111, 197, 232, 0.38) 30%, rgba(65, 120, 132, 0) 72%);
  filter: blur(32rpx);
  opacity: 0.9;
}

.chat-ticket-reveal-card__card {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 42rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow:
    0 0 64rpx rgba(255, 255, 255, 0.8),
    0 8rpx 8rpx rgba(0, 0, 0, 0.25),
    8rpx 8rpx 80rpx rgba(0, 0, 0, 0.4);
}

.chat-ticket-reveal-card__image,
.chat-ticket-reveal-card__placeholder {
  width: 100%;
  height: 100%;
}

.chat-ticket-reveal-card__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(196, 224, 255, 0.08) 100%),
    rgba(7, 39, 67, 0.42);
}

.chat-ticket-reveal-card__placeholder-text {
  color: $anima-text-dim;
  font-family: $anima-font-display;
  font-size: 28rpx;
  letter-spacing: 2rpx;
}

.chat-ticket-reveal-card__accept {
  position: absolute;
  left: 50%;
  top: 71.9%;
  width: 212rpx;
  height: 72rpx;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid rgba(230, 248, 255, 0.48);
  border-radius: 36rpx;
  background: rgba(0, 0, 0, 0);
  transition: opacity 180ms ease, transform 180ms ease;
}

.chat-ticket-reveal-card__accept::before,
.chat-ticket-reveal-card__accept::after {
  content: "";
  position: absolute;
  top: -2rpx;
  width: 54rpx;
  height: 14rpx;
  border-radius: 2rpx;
  background: linear-gradient(180deg, rgba(22, 59, 102, 0.92) 0%, rgba(7, 39, 67, 0.72) 100%);
}

.chat-ticket-reveal-card__accept::before {
  left: 48rpx;
}

.chat-ticket-reveal-card__accept::after {
  right: 48rpx;
}

.chat-ticket-reveal-card__accept-text {
  color: $anima-text-main;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 32rpx;
  letter-spacing: 1rpx;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.chat-ticket-reveal-card__reroll {
  position: absolute;
  left: 50%;
  top: 81.7%;
  width: 160rpx;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  transition: opacity 180ms ease, transform 180ms ease;
}

.chat-ticket-reveal-card__reroll-icon {
  width: 46rpx;
  height: 46rpx;
}

.chat-ticket-reveal-card__reroll-text {
  color: $anima-text-dim;
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 40rpx;
  letter-spacing: 1rpx;
}

.chat-ticket-reveal-card__accept--disabled,
.chat-ticket-reveal-card__reroll--disabled {
  opacity: $anima-button-disabled;
}

.chat-ticket-reveal-card__button--hover {
  opacity: 0.82;
  transform: translateX(-50%) translateY(-2rpx);
}

.chat-ticket-reveal-card__reroll.chat-ticket-reveal-card__button--hover {
  transform: translateX(-50%) translateY(-2rpx);
}

@media screen and (max-width: 360px) {
  .chat-ticket-reveal-card__card-shell {
    width: 60.5%;
    left: 19.75%;
  }

  .chat-ticket-reveal-card__prompt {
    width: 76%;
    left: 18%;
  }
}
</style>

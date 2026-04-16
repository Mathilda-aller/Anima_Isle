<script setup lang="ts">
import { AUTH_ASSETS } from "@/modules/auth/assets";

const props = withDefaults(
  defineProps<{
    badge?: string;
    travelDays?: string;
    title?: string;
    islandsVisited?: string;
    selected?: boolean;
  }>(),
  {
    badge: "PASSENGER ID",
    travelDays: "travel day",
    title: "拾光者",
    islandsVisited: "已旅行过20座岛屿",
    selected: false,
  },
);
</script>

<template>
  <view class="resident-pass-card" :class="{ 'resident-pass-card--selected': props.selected }">
    <image class="resident-pass-card__shell" :src="AUTH_ASSETS.resident.passShell" mode="aspectFit" />
    <view class="resident-pass-card__content">
      <text class="resident-pass-card__brand">言屿</text>
      <view class="resident-pass-card__meta resident-pass-card__meta--left">
        <text>{{ props.badge }}</text>
      </view>
      <view class="resident-pass-card__meta resident-pass-card__meta--right">
        <text>{{ props.travelDays }}</text>
      </view>
      <view class="resident-pass-card__divider resident-pass-card__divider--horizontal"></view>
      <view class="resident-pass-card__divider resident-pass-card__divider--vertical"></view>
      <text class="resident-pass-card__title">{{ props.title }}</text>
      <text class="resident-pass-card__count">{{ props.islandsVisited }}</text>
      <view class="resident-pass-card__stamp"></view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.resident-pass-card {
  position: relative;
  width: 100%;
  aspect-ratio: 156.0407 / 84;
  filter: drop-shadow(0 12rpx 28rpx rgba(0, 0, 0, 0.2));
  transition: transform 0.2s ease, opacity 0.2s ease, filter 0.2s ease;
}

.resident-pass-card--selected {
  transform: translateY(-4rpx) scale(1.015);
  filter: drop-shadow(0 18rpx 44rpx rgba(132, 189, 255, 0.3));
}

.resident-pass-card__shell {
  width: 100%;
  height: 100%;
}

.resident-pass-card__content {
  position: absolute;
  inset: 0;
  padding: 10rpx 12rpx 12rpx;
  color: $anima-text-main;
  font-family: $anima-font-display;
}

.resident-pass-card__brand {
  position: absolute;
  top: 10rpx;
  left: 56rpx;
  font-size: 10rpx;
  line-height: 1.2;
  opacity: 0.4;
  text-shadow: $anima-shadow-title;
}

.resident-pass-card__meta {
  position: absolute;
  top: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $anima-text-strong;
  text-align: center;
  letter-spacing: 1rpx;
}

.resident-pass-card__meta text {
  font-size: 8rpx;
  line-height: 1.25;
  white-space: pre-line;
}

.resident-pass-card__meta--left {
  left: 12rpx;
  width: 34rpx;
}

.resident-pass-card__meta--right {
  left: 92rpx;
  width: 34rpx;
}

.resident-pass-card__divider {
  position: absolute;
  background: rgba(255, 255, 255, 0.28);
}

.resident-pass-card__divider--horizontal {
  left: 72rpx;
  top: 50rpx;
  width: 56rpx;
  height: 1rpx;
  opacity: 0.55;
}

.resident-pass-card__divider--vertical {
  left: 64rpx;
  top: 50rpx;
  width: 1rpx;
  height: 34rpx;
  opacity: 0.55;
}

.resident-pass-card__title {
  position: absolute;
  left: 16rpx;
  top: 64rpx;
  width: 34rpx;
  font-size: 14rpx;
  line-height: 1.15;
  text-align: center;
  letter-spacing: 1rpx;
}

.resident-pass-card__count {
  position: absolute;
  left: 88rpx;
  top: 64rpx;
  width: 54rpx;
  font-size: 9rpx;
  line-height: 1.2;
  text-align: center;
  letter-spacing: 0.8rpx;
}

.resident-pass-card__stamp {
  position: absolute;
  right: 22rpx;
  bottom: 12rpx;
  width: 18rpx;
  height: 18rpx;
  border-radius: 6rpx;
  background: rgba(255, 255, 255, 0.18);
}
</style>

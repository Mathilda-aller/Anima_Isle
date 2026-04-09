<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    label: string;
    avatarSrc?: string;
  }>(),
  {
    avatarSrc: "",
  },
);
</script>

<template>
  <view class="island-tag-chip">
    <view v-if="avatarSrc" class="island-tag-chip__avatar-shell">
      <image class="island-tag-chip__avatar" :src="avatarSrc" mode="aspectFill" />
    </view>
    <text class="island-tag-chip__label">{{ label }}</text>
  </view>
</template>

<style scoped lang="scss">
.island-tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  min-height: 54rpx;
  padding: 0 22rpx 0 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.03);
  box-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.island-tag-chip__avatar-shell {
  width: 34rpx;
  height: 34rpx;
  border-radius: 30rpx;
  overflow: hidden;
  background: #ffffff;
}

.island-tag-chip__avatar {
  width: 100%;
  height: 100%;
  border-radius: 30rpx;
}

.island-tag-chip__label {
  color: var(--anima-text-dim);
  font-size: 22rpx;
  line-height: 44rpx;
  letter-spacing: 1rpx;
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
}
</style>

<script setup lang="ts">
defineProps<{
  label: string;
  icon: string;
  glowImage: string;
}>();
</script>

<template>
  <view class="action-button">
    <image class="halo-image" :src="glowImage" mode="aspectFill" />
    <image class="icon" :src="icon" mode="aspectFit" />
    <text class="label">{{ label }}</text>
  </view>
</template>

<style scoped lang="scss">
.action-button {
  width: 170rpx;
  height: 170rpx;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.halo-image {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  width: 100%;
  height: 100%;
  opacity: 0.95;
}

.icon {
  width: 44rpx;
  height: 44rpx;
  z-index: 1;
}

.label {
  margin-top: 12rpx;
  font-size: var(--anima-font-body);
  color: var(--anima-text-main);
  letter-spacing: 6rpx;
  z-index: 1;
  font-family: var(--anima-font-display);
}
</style>

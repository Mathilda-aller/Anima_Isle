<script setup lang="ts">
defineProps<{
  label: string;
  underlineSrc: string;
}>();

const emit = defineEmits<{
  (e: "click"): void;
}>();
</script>

<template>
  <view class="switch-wrap" hover-class="switch-wrap-hover" @click="emit('click')">
    <text class="switch-text">{{ label }}</text>
    <image class="switch-line" :src="underlineSrc" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.switch-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.switch-text {
  color: $anima-text-dim;
  font-size: 40rpx;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
}

.switch-line {
  margin-top: 8rpx;
  width: 202rpx;
  height: 8rpx;
}

.switch-wrap-hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}
</style>

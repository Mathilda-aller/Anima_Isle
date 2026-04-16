<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string;
    glowImage?: string;
    micBody?: string;
    micHead?: string;
  }>(),
  {
    label: "语音输入",
    glowImage: "",
    micBody: "",
    micHead: "",
  },
);
</script>

<template>
  <view class="voice-input-button">
    <image v-if="glowImage" class="glow-image" :src="glowImage" mode="aspectFill" />

    <view class="mic-icon">
      <image v-if="micBody" class="mic-body" :src="micBody" mode="aspectFit" />
      <image v-if="micHead" class="mic-head" :src="micHead" mode="aspectFit" />
    </view>

    <text class="label">{{ label }}</text>
  </view>
</template>

<style scoped lang="scss">
.voice-input-button {
  width: 170rpx;
  height: 170rpx;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.glow-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  opacity: 0.95;
}

.mic-icon {
  position: relative;
  width: 46rpx;
  height: 46rpx;
  z-index: 1;
}

.mic-body {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.mic-head {
  position: absolute;
  left: 50%;
  top: -6rpx;
  width: 20rpx;
  height: 20rpx;
  transform: translateX(-50%);
}

.label {
  margin-top: 12rpx;
  font-size: $anima-font-body;
  color: $anima-text-float;
  letter-spacing: 6rpx;
  z-index: 1;
  font-family: $anima-font-display;
}
</style>

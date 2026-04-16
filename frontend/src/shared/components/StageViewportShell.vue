<script setup lang="ts">
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";

withDefaults(
  defineProps<{
    viewportMaxWidth?: string;
    textureOpacity?: number;
  }>(),
  {
    viewportMaxWidth: "820rpx",
    textureOpacity: 0.55,
  },
);
</script>

<template>
  <view class="stage-viewport-shell">
    <view class="stage-viewport-shell__viewport" :style="{ maxWidth: viewportMaxWidth }">
      <DarkBackgroundLayer :texture-opacity="textureOpacity" />
      <slot />
    </view>
  </view>
</template>

<style scoped lang="scss">
.stage-viewport-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #072743 0%, #2c417a 49.52%, #3f4376 100%);
}

.stage-viewport-shell__viewport {
  position: relative;
  width: 100%;
  min-height: 100vh;
  margin: 0 auto;
  overflow: hidden;
  z-index: 1;
}
</style>

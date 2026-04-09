<script setup lang="ts">
import { SHARED_ASSETS } from "@/shared/assets";

withDefaults(
  defineProps<{
    textureOpacity?: number;
  }>(),
  {
    textureOpacity: 0.3,
  },
);
</script>

<template>
  <view class="dark-background-layer">
    <image
      class="dark-background-layer__texture"
      :style="{ opacity: String(textureOpacity) }"
      :src="SHARED_ASSETS.bg.darkBg"
      mode="aspectFill"
    />
  </view>
</template>

<style scoped lang="scss">
.dark-background-layer {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.dark-background-layer__texture {
  position: absolute;
  left: -15.67%;
  top: -1.26%;
  width: 123.88%;
  height: 101.26%;
  filter: saturate(0.9) brightness(0.82);
}
</style>

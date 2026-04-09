<script setup lang="ts">
import { SHARED_ASSETS } from "@/shared/assets";

withDefaults(
  defineProps<{
    animated?: boolean;
  }>(),
  {
    animated: true,
  },
);
</script>

<template>
  <view class="night-ip" :class="{ 'night-ip--animated': animated }">
    <view class="night-ip__ratio"></view>
    <image class="night-ip__head night-ip__head--back" :src="SHARED_ASSETS.icons.ipNightHeadBack" mode="aspectFit" />
    <image class="night-ip__head night-ip__head--front" :src="SHARED_ASSETS.icons.ipNightHeadFront" mode="aspectFit" />
    <image class="night-ip__face" :src="SHARED_ASSETS.icons.ipFaceVector" mode="aspectFit" />
    <image class="night-ip__eye night-ip__eye--left" :src="SHARED_ASSETS.icons.ipEyeEllipse" mode="aspectFit" />
    <image class="night-ip__eye night-ip__eye--right" :src="SHARED_ASSETS.icons.ipEyeEllipse" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.night-ip {
  position: relative;
  display: block;
  width: 100%;
  max-width: 100%;
  flex-shrink: 0;
}

.night-ip__ratio {
  width: 100%;
  padding-top: 63.31%;
}

.night-ip--animated {
  transform-origin: center bottom;
  animation: night-ip-breathe 4.2s ease-in-out infinite;
  will-change: transform, opacity;
}

.night-ip__head {
  position: absolute;
  top: 0;
  display: block;
  pointer-events: none;
}

.night-ip__head--back {
  left: 8.47%;
  top: 7.96%;
  width: 82.96%;
  height: 71.17%;
}

.night-ip__head--front {
  left: 8.47%;
  top: 7.96%;
  width: 78.94%;
  height: 71.17%;
}

.night-ip__face {
  position: absolute;
  left: 22.38%;
  top: 29.2%;
  width: 53.17%;
  height: 53.31%;
  pointer-events: none;
}

.night-ip__eye {
  position: absolute;
  top: 55.75%;
  width: 2.24%;
  height: 7.52%;
  pointer-events: none;
}

.night-ip__eye--left {
  left: 41.46%;
}

.night-ip__eye--right {
  left: 53.5%;
}

@keyframes night-ip-breathe {
  0%,
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  50% {
    transform: translateY(-8rpx) scale(1.016);
    opacity: 0.96;
  }
}
</style>

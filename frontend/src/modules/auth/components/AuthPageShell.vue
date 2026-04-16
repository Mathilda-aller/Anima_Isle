<script setup lang="ts">
import { AUTH_ASSETS } from "@/modules/auth/assets";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";

defineProps<{
  title: string;
  subtitle: string;
  errorMsg?: string;
}>();
</script>

<template>
  <StageViewportShell>
    <view class="content">
      <image class="ip-logo" :src="AUTH_ASSETS.illustrations.islandIpLogo" mode="aspectFit" />
      <text class="title">{{ title }}</text>
      <text class="subtitle">{{ subtitle }}</text>

      <view class="form-slot">
        <slot name="form" />
      </view>

      <view class="action-slot">
        <slot name="action" />
      </view>

      <view class="switch-slot">
        <slot name="switch" />
      </view>

      <text v-if="errorMsg" class="error">{{ errorMsg }}</text>

      <slot name="overlay" />
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.content {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  padding: calc(140rpx + env(safe-area-inset-top)) 56rpx calc(74rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ip-logo {
  width: 212rpx;
  height: 256rpx;
}

.title {
  margin-top: 56rpx;
  color: $anima-text-strong;
  font-size: $anima-font-title;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
  text-align: center;
}

.subtitle {
  margin-top: 10rpx;
  color: $anima-text-muted;
  letter-spacing: 3rpx;
  font-size: $anima-font-subtitle;
  font-family: $anima-font-display;
  text-align: center;
}

.form-slot {
  width: 100%;
}

.action-slot {
  width: 100%;
  display: flex;
  justify-content: center;
}

.switch-slot {
  margin-top: auto;
  width: 100%;
  display: flex;
  justify-content: center;
}

.error {
  margin-top: 18rpx;
  color: $anima-text-error;
  text-align: center;
}
</style>

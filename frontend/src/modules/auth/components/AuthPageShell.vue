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
      <view class="auth-page-shell__halo" />
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
  isolation: isolate;
  z-index: 1;
  min-height: 100vh;
  padding: calc(140rpx + env(safe-area-inset-top)) 56rpx calc(74rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  align-items: center;
}

.content > :not(.auth-page-shell__halo) {
  position: relative;
  z-index: 1;
}

.auth-page-shell__halo {
  position: absolute;
  left: 50%;
  top: 60%;
  width: 694rpx;
  height: 694rpx;
  border-radius: 50%;
  background: var(--anima-glow-auth);
  filter: blur(128rpx);
  mix-blend-mode: screen;
  pointer-events: none;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.ip-logo {
  width: 212rpx;
  height: 256rpx;
}

.title {
  margin-top: 56rpx;
  color: var(--anima-text-strong);
  font-size: var(--anima-font-title);
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
  text-align: center;
}

.subtitle {
  margin-top: 10rpx;
  color: var(--anima-text-muted);
  letter-spacing: 3rpx;
  font-size: var(--anima-font-subtitle);
  font-family: var(--anima-font-display);
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
  color: var(--anima-text-error);
  text-align: center;
}
</style>

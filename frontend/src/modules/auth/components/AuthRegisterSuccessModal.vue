<script setup lang="ts">
import { AUTH_ASSETS } from "@/modules/auth/assets";

const emit = defineEmits<{
  (e: "close"): void;
  (e: "confirm"): void;
}>();
</script>

<template>
  <view class="register-success-modal">
    <view class="register-success-modal__scrim" />

    <view class="register-success-modal__panel">
      <view class="register-success-modal__close" hover-class="register-success-modal__close--hover" @click="emit('close')">
        <image class="register-success-modal__close-icon" :src="AUTH_ASSETS.icons.registerSuccessClose" mode="aspectFit" />
      </view>

      <view class="register-success-modal__badge">
        <view class="register-success-modal__badge-glow" />
        <view class="register-success-modal__badge-core">
          <image
            class="register-success-modal__badge-icon"
            :src="AUTH_ASSETS.icons.registerSuccessCheckmark"
            mode="aspectFit"
          />
        </view>
      </view>

      <text class="register-success-modal__title">注册成功</text>
      <view class="register-success-modal__copy">
        <text class="register-success-modal__copy-line">欢迎加入言屿！</text>
        <text class="register-success-modal__copy-line">您的账号已创建成功</text>
      </view>

      <button
        class="register-success-modal__button"
        hover-class="register-success-modal__button--hover"
        @click="emit('confirm')"
      >
        <text class="register-success-modal__button-text">开始探索</text>
      </button>
    </view>
  </view>
</template>

<style scoped lang="scss">
.register-success-modal {
  position: absolute;
  inset: 0;
  z-index: 20;
}

.register-success-modal__scrim {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
}

.register-success-modal__panel {
  position: absolute;
  left: 50%;
  top: 491rpx;
  width: 640rpx;
  height: 671rpx;
  transform: translateX(-50%);
  border-radius: 48rpx;
  border: 1.386rpx solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(133.66deg, rgba(63, 67, 118, 0.95) 0%, rgba(44, 65, 122, 0.95) 100%);
  box-shadow: 0 0 96rpx rgba(116, 212, 234, 0.4);
  backdrop-filter: blur(20rpx);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.register-success-modal__close {
  position: absolute;
  top: 32rpx;
  right: 32rpx;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.register-success-modal__close-icon {
  width: 28rpx;
  height: 28rpx;
}

.register-success-modal__badge {
  position: relative;
  margin-top: 64rpx;
  width: 160rpx;
  height: 160rpx;
}

.register-success-modal__badge-glow {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(116, 212, 234, 1) 0%, rgba(90, 166, 183, 1) 100%);
  filter: blur(48rpx);
  opacity: 0.2;
}

.register-success-modal__badge-core {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.386rpx solid rgba(116, 212, 234, 0.5);
  background: linear-gradient(135deg, rgba(116, 212, 234, 0.3) 0%, rgba(90, 166, 183, 0.3) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-success-modal__badge-icon {
  width: 96rpx;
  height: 96rpx;
}

.register-success-modal__title {
  margin-top: 48rpx;
  color: #e0f0ff;
  font-size: 48rpx;
  line-height: 72rpx;
  letter-spacing: 1rpx;
  font-family: var(--anima-font-display);
}

.register-success-modal__copy {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.register-success-modal__copy-line {
  color: rgba(255, 255, 255, 0.7);
  font-size: 28rpx;
  line-height: 44rpx;
  letter-spacing: 1rpx;
  font-family: var(--anima-font-display);
}

.register-success-modal__button {
  margin-top: 64rpx;
  width: 510rpx;
  height: 84rpx;
  overflow: hidden;
  border-radius: 100rpx;
  border: var(--anima-button-border);
  background: var(--anima-button-bg);
  box-shadow: var(--anima-button-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  -webkit-appearance: none;
  appearance: none;
}

.register-success-modal__button::after {
  border: none;
}

.register-success-modal__button-text {
  color: #e6f8ff;
  font-size: 32rpx;
  line-height: 48rpx;
  letter-spacing: 1rpx;
  font-family: var(--anima-font-display);
}

.register-success-modal__close--hover,
.register-success-modal__button--hover {
  opacity: 0.82;
  transform: scale(0.98);
}
</style>

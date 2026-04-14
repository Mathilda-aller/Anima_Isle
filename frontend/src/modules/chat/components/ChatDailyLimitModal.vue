<script setup lang="ts">
const emit = defineEmits<{
  (e: "confirm"): void;
}>();
</script>

<template>
  <view class="chat-daily-limit-modal">
    <view class="chat-daily-limit-modal__scrim" />

    <view class="chat-daily-limit-modal__panel">
      <view class="chat-daily-limit-modal__badge">
        <view class="chat-daily-limit-modal__badge-glow" />
        <view class="chat-daily-limit-modal__badge-core">
          <view class="chat-daily-limit-modal__moon">
            <view class="chat-daily-limit-modal__moon-shadow" />
          </view>
          <view class="chat-daily-limit-modal__star" />
        </view>
      </view>

      <text class="chat-daily-limit-modal__title">今天先歇一歇</text>
      <view class="chat-daily-limit-modal__copy">
        <text class="chat-daily-limit-modal__copy-line">今天已经有点累了，</text>
        <text class="chat-daily-limit-modal__copy-line">明天再来和我聊聊吧~</text>
      </view>

      <button
        class="chat-daily-limit-modal__button"
        hover-class="chat-daily-limit-modal__button--hover"
        @click="emit('confirm')"
      >
        <text class="chat-daily-limit-modal__button-text">返回</text>
      </button>
    </view>
  </view>
</template>

<style scoped lang="scss">
.chat-daily-limit-modal {
  position: absolute;
  inset: 0;
  z-index: 20;
}

.chat-daily-limit-modal__scrim {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 44%, rgba(116, 212, 234, 0.14) 0%, rgba(116, 212, 234, 0) 42%),
    rgba(3, 10, 27, 0.5);
  backdrop-filter: blur(10rpx);
}

.chat-daily-limit-modal__panel {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 640rpx;
  min-height: 612rpx;
  transform: translate(-50%, -50%);
  border-radius: 48rpx;
  border: 1.386rpx solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(133.66deg, rgba(63, 67, 118, 0.95) 0%, rgba(44, 65, 122, 0.95) 100%);
  box-shadow: 0 0 96rpx rgba(116, 212, 234, 0.4);
  backdrop-filter: blur(20rpx);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx 32rpx 56rpx;
}

.chat-daily-limit-modal__badge {
  position: relative;
  width: 160rpx;
  height: 160rpx;
}

.chat-daily-limit-modal__badge-glow {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(116, 212, 234, 1) 0%, rgba(90, 166, 183, 1) 100%);
  filter: blur(48rpx);
  opacity: 0.2;
}

.chat-daily-limit-modal__badge-core {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.386rpx solid rgba(116, 212, 234, 0.5);
  background: linear-gradient(135deg, rgba(116, 212, 234, 0.3) 0%, rgba(90, 166, 183, 0.3) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-daily-limit-modal__moon {
  position: relative;
  width: 58rpx;
  height: 58rpx;
  border-radius: 50%;
  background: rgba(191, 246, 255, 0.92);
  box-shadow: 0 0 20rpx rgba(191, 246, 255, 0.25);
}

.chat-daily-limit-modal__moon-shadow {
  position: absolute;
  top: 4rpx;
  right: -2rpx;
  width: 46rpx;
  height: 46rpx;
  border-radius: 50%;
  background: rgba(92, 148, 184, 0.95);
}

.chat-daily-limit-modal__star {
  position: absolute;
  top: 46rpx;
  right: 40rpx;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: rgba(230, 248, 255, 0.92);
  box-shadow:
    0 0 0 5rpx rgba(230, 248, 255, 0.08),
    0 0 12rpx rgba(230, 248, 255, 0.5);
}

.chat-daily-limit-modal__title {
  margin-top: 48rpx;
  color: var(--anima-text-strong);
  font-size: 48rpx;
  line-height: 72rpx;
  letter-spacing: 1rpx;
  font-family: var(--anima-font-display);
}

.chat-daily-limit-modal__copy {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.chat-daily-limit-modal__copy-line {
  color: rgba(255, 255, 255, 0.7);
  font-size: 28rpx;
  line-height: 44rpx;
  letter-spacing: 1rpx;
  font-family: var(--anima-font-display);
}

.chat-daily-limit-modal__button {
  margin-top: 72rpx;
  width: 100%;
  height: 84rpx;
  border-radius: 100rpx;
  border: 1.386rpx solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(90deg, rgba(116, 212, 234, 0.2) 0%, rgba(90, 166, 183, 0.2) 100%);
  box-shadow: 0 0 48rpx rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.chat-daily-limit-modal__button::after {
  border: none;
}

.chat-daily-limit-modal__button-text {
  color: var(--anima-text-main);
  font-size: 32rpx;
  line-height: 48rpx;
  letter-spacing: 1rpx;
  font-family: var(--anima-font-display);
}

.chat-daily-limit-modal__button--hover {
  opacity: 0.82;
  transform: scale(0.98);
}
</style>

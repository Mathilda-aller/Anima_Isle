<script setup lang="ts">
defineProps<{
  label: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (e: "click"): void;
}>();
</script>

<template>
  <button class="login-btn" hover-class="auth-btn-hover" :disabled="disabled" @click="emit('click')">
    <text class="login-btn-text">{{ label }}</text>
  </button>
</template>

<style scoped lang="scss">
.login-btn {
  width: 180rpx;
  height: 66rpx;
  position: relative;
  overflow: hidden;
  border-radius: 30rpx;
  border: var(--anima-button-border);
  background: var(--anima-button-bg);
  box-shadow: var(--anima-button-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  -webkit-appearance: none;
  appearance: none;
  transition: opacity 180ms ease, transform 180ms ease, box-shadow 180ms ease;
}

.login-btn::before {
  content: "";
  position: absolute;
  inset: 1rpx;
  border-radius: inherit;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.01) 100%);
  pointer-events: none;
}

.login-btn::after {
  border: none;
}

.login-btn[disabled] {
  opacity: var(--anima-button-disabled);
}

.login-btn-text {
  position: relative;
  z-index: 1;
  color: var(--anima-text-main);
  font-size: 32rpx;
  letter-spacing: 1rpx;
  line-height: 56rpx;
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
}

.auth-btn-hover {
  opacity: 0.82;
  transform: translateY(2rpx) scale(0.98);
}
</style>

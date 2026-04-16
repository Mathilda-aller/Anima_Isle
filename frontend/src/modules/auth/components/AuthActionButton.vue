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
  border-radius: 15rpx;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.login-btn::after {
  border: none;
}

.login-btn[disabled] {
  opacity: $anima-button-disabled;
}

.login-btn-text {
  color: $anima-text-main;
  font-size: 32rpx;
  letter-spacing: 1rpx;
  line-height: 1;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
}

.auth-btn-hover {
  opacity: 0.82;
  transform: scale(0.98);
}
</style>

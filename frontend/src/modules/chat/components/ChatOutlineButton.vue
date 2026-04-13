<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    disabled?: boolean;
  }>(),
  {
    disabled: false,
  },
);

defineEmits<{
  (e: "click"): void;
}>();
</script>

<template>
  <button class="chat-outline-button" :class="{ 'chat-outline-button--disabled': disabled }" :disabled="disabled" hover-class="button-hover" @click="$emit('click')">
    {{ label }}
  </button>
</template>

<style scoped lang="scss">
.chat-outline-button {
  width: 100%;
  height: 100%;
  padding: 0;
  overflow: hidden;
  border-radius: var(--anima-radius-pill);
  border: var(--anima-button-border);
  background: var(--anima-button-bg);
  box-shadow: var(--anima-button-glow);
  color: var(--anima-text-main);
  font-size: 32rpx;
  line-height: 66rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
  -webkit-appearance: none;
  appearance: none;
}

.chat-outline-button::after {
  border: none;
}

.chat-outline-button--disabled {
  opacity: var(--anima-button-disabled);
}

.button-hover {
  opacity: 0.88;
  transform: translateY(2rpx) scale(0.98);
}
</style>

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
  border-radius: $anima-radius-pill;
  border: 1rpx solid rgba(230, 248, 255, 0.34);
  background: transparent;
  color: $anima-text-main;
  font-size: 32rpx;
  line-height: 66rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
}

.chat-outline-button::after {
  border: none;
}

.chat-outline-button--disabled {
  opacity: $anima-button-disabled;
}

.button-hover {
  opacity: 0.88;
}
</style>

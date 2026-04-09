<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  modelValue: string;
  type?: "text" | "password";
  placeholder: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

function onInput(event: Event) {
  const value = ((event as any)?.detail?.value || "") as string;
  emit("update:modelValue", value);
}

const isFocused = ref(false);
</script>

<template>
  <view class="field-wrap" :class="{ 'field-wrap--focused': isFocused }">
    <input
      :value="modelValue"
      class="field"
      :type="type || 'text'"
      :placeholder="placeholder"
      placeholder-class="field-placeholder"
      @input="onInput"
      @focus="isFocused = true"
      @blur="isFocused = false"
    />
  </view>
</template>

<style scoped lang="scss">
.field-wrap {
  width: 100%;
  height: 86rpx;
  border-radius: var(--anima-radius-pill);
  background: var(--anima-surface-field);
  box-shadow: var(--anima-shadow-field-soft);
  border: 1rpx solid var(--anima-line-field);
  overflow: hidden;
  transition: box-shadow 0.22s ease, border-color 0.22s ease, background-color 0.22s ease;
}

.field-wrap--focused {
  background: var(--anima-surface-field-focus);
  border-color: var(--anima-line-focus);
  box-shadow: var(--anima-shadow-field-focus);
}

.field {
  width: 100%;
  height: 100%;
  padding: 0 46rpx;
  color: var(--anima-text-main);
  font-size: var(--anima-font-body);
  letter-spacing: 2rpx;
  font-family: var(--anima-font-display);
  background: transparent;
}

.field-placeholder {
  color: var(--anima-text-placeholder);
  font-size: var(--anima-font-body);
  letter-spacing: 2.4rpx;
  font-family: var(--anima-font-display);
}
</style>

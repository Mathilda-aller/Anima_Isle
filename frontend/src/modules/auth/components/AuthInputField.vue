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

function extractValue(event: unknown): string {
  if (typeof event === "string") {
    return event;
  }
  const value =
    (event as { detail?: { value?: unknown } } | undefined)?.detail?.value ??
    (event as { target?: { value?: unknown } } | undefined)?.target?.value ??
    (event as { detail?: unknown } | undefined)?.detail ??
    "";
  return typeof value === "string" ? value : String(value ?? "");
}

function onInput(event: unknown) {
  const value = extractValue(event);
  emit("update:modelValue", value);
}

function onBlur(event: unknown) {
  isFocused.value = false;
  emit("update:modelValue", extractValue(event));
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
      @change="onInput"
      @focus="isFocused = true"
      @blur="onBlur"
    />
  </view>
</template>

<style scoped lang="scss">
.field-wrap {
  width: 100%;
  height: 86rpx;
  border-radius: $anima-radius-pill;
  background: $anima-surface-field;
  box-shadow: $anima-shadow-field-soft;
  border: 1rpx solid $anima-line-field;
  overflow: hidden;
  transition: box-shadow 0.22s ease, border-color 0.22s ease, background-color 0.22s ease;
}

.field-wrap--focused {
  background: $anima-surface-field-focus;
  border-color: $anima-line-focus;
  box-shadow: $anima-shadow-field-focus;
}

.field {
  width: 100%;
  height: 100%;
  padding: 0 46rpx;
  color: $anima-text-main;
  font-size: $anima-font-body;
  letter-spacing: 2rpx;
  font-family: $anima-font-display;
  background: transparent;
}

.field-placeholder {
  color: $anima-text-placeholder;
  font-size: $anima-font-body;
  letter-spacing: 2.4rpx;
  font-family: $anima-font-display;
}
</style>

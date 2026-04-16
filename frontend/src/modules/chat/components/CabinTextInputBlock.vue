<script setup lang="ts">
import { CHAT_ASSETS } from "@/modules/chat/assets";
import ChatOutlineButton from "@/modules/chat/components/ChatOutlineButton.vue";

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    placeholder?: string;
    showVoiceIcon?: boolean;
    showSubmit?: boolean;
    inputDisabled?: boolean;
    submitDisabled?: boolean;
    submitLabel?: string;
    inputMinHeight?: string;
    textareaHeight?: string;
    inputMaxLength?: number;
    focusInput?: boolean;
    transitioning?: boolean;
    composerGap?: string;
  }>(),
  {
    modelValue: "",
    placeholder: "这一刻，想写下什么…",
    showVoiceIcon: true,
    showSubmit: true,
    inputDisabled: false,
    submitDisabled: false,
    submitLabel: "写好了",
    inputMinHeight: "70rpx",
    textareaHeight: "70rpx",
    inputMaxLength: 200,
    focusInput: false,
    transitioning: false,
    composerGap: "64rpx",
  },
);

const emit = defineEmits<{
  (e: "submit"): void;
  (e: "focus"): void;
  (e: "voice"): void;
  (e: "update:modelValue", value: string): void;
}>();

function onInput(event: Event) {
  const detail = (event as Event & { detail?: { value?: string } }).detail;
  emit("update:modelValue", detail?.value ?? "");
}
</script>

<template>
  <view
    class="cabin-text-input-block"
    :class="{ 'cabin-text-input-block--fade': transitioning }"
    :style="{ gap: composerGap }"
  >
    <view class="cabin-text-input-block__composer" :style="{ minHeight: inputMinHeight }">
      <textarea
        :value="modelValue"
        class="cabin-text-input-block__textarea"
        :style="{ height: textareaHeight }"
        :maxlength="inputMaxLength"
        :placeholder="placeholder"
        placeholder-class="cabin-text-input-block__placeholder"
        :disabled="inputDisabled"
        :focus="focusInput"
        confirm-type="done"
        @input="onInput"
        @focus="emit('focus')"
      />
      <image
        class="cabin-text-input-block__underline"
        :src="CHAT_ASSETS.icons.chatInputUnderline"
        mode="scaleToFill"
      />
      <image
        v-if="showVoiceIcon"
        class="cabin-text-input-block__voice-icon"
        :src="CHAT_ASSETS.icons.voiceBody"
        mode="aspectFit"
        @click="emit('voice')"
      />
    </view>

    <view v-if="showSubmit" class="cabin-text-input-block__submit">
      <ChatOutlineButton :label="submitLabel" :disabled="submitDisabled" @click="emit('submit')" />
    </view>
  </view>
</template>

<style scoped lang="scss">
.cabin-text-input-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 64rpx;
  transition: opacity 220ms ease, transform 220ms ease;
}

.cabin-text-input-block--fade {
  opacity: 0;
  transform: translateY(10rpx);
}

.cabin-text-input-block__composer {
  position: relative;
  width: 100%;
}

.cabin-text-input-block__textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 70rpx;
  max-height: 220rpx;
  padding: 6rpx 10.48% 8rpx 0;
  background: transparent;
  color: $anima-text-main;
  font-size: 32rpx;
  line-height: 56rpx;
  text-align: center;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
  letter-spacing: 1rpx;
  overflow-y: auto;
}

.cabin-text-input-block__placeholder {
  color: $anima-text-dim;
  text-align: center;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  white-space: nowrap;
}

.cabin-text-input-block__underline {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 2rpx;
  opacity: 0.8;
}

.cabin-text-input-block__voice-icon {
  position: absolute;
  right: 0;
  top: 11.43%;
  width: 8.89%;
  height: 79.97%;
  opacity: 0.78;
}

.cabin-text-input-block__submit {
  width: 142rpx;
  height: 66rpx;
}
</style>

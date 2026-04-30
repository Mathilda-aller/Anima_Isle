<script setup lang="ts">
import { computed } from "vue";
import { CHAT_ASSETS } from "@/modules/chat/assets";

const props = withDefaults(
  defineProps<{
    variant?: "stop" | "review";
  }>(),
  {
    variant: "stop",
  },
);

defineEmits<{
  (e: "click"): void;
}>();

const buttonIcon = computed(() =>
  props.variant === "review" ? CHAT_ASSETS.icons.voiceReview : CHAT_ASSETS.icons.voiceEndChat,
);
</script>

<template>
  <view class="voice-end-chat-button" hover-class="voice-end-chat-button--hover" @click="$emit('click')">
    <image class="voice-end-chat-button__image" :src="buttonIcon" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.voice-end-chat-button {
  width: 150rpx;
  height: 150rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-end-chat-button__image {
  width: 150rpx;
  height: 150rpx;
}

.voice-end-chat-button--hover {
  opacity: 0.86;
  transform: scale(0.985);
}
</style>

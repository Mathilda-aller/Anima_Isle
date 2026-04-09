<script setup lang="ts">
import { CHAT_ASSETS } from "@/modules/chat/assets";

defineEmits<{
  (e: "click"): void;
}>();
</script>

<template>
  <view class="voice-end-chat-button" hover-class="voice-end-chat-button--hover" @click="$emit('click')">
    <image class="voice-end-chat-button__image" :src="CHAT_ASSETS.icons.voiceEndChat" mode="aspectFit" />
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

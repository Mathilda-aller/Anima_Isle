<script setup lang="ts">
import { computed } from "vue";
import { CHAT_ASSETS } from "@/modules/chat/assets";
import ChatOutlineButton from "@/modules/chat/components/ChatOutlineButton.vue";
import VoiceEndChatButton from "@/modules/chat/components/VoiceEndChatButton.vue";

const props = withDefaults(
  defineProps<{
    statusText?: string;
    durationText?: string;
    recording?: boolean;
    processing?: boolean;
    transitioning?: boolean;
    showMeta?: boolean;
    showActions?: boolean;
    showPrimaryControls?: boolean;
    confirmDisabled?: boolean;
    cancelLabel?: string;
    confirmLabel?: string;
    showWriteEntry?: boolean;
    rippleIntensity?: number;
  }>(),
  {
    statusText: "轻触开始说话",
    durationText: "00:00",
    recording: false,
    processing: false,
    transitioning: false,
    showMeta: true,
    showActions: false,
    showPrimaryControls: true,
    confirmDisabled: false,
    cancelLabel: "取消",
    confirmLabel: "完成",
    showWriteEntry: true,
    rippleIntensity: 0,
  },
);

const emit = defineEmits<{
  (e: "toggle"): void;
  (e: "cancel"): void;
  (e: "confirm"): void;
  (e: "write"): void;
}>();

const liveStatusText = computed(() => {
  if (props.processing) return "正在整理你的声音…";
  if (props.recording) return props.statusText || "正在倾听";
  return props.statusText || "轻触开始说话";
});

const rippleStyle = computed(() => {
  const intensity = Math.min(Math.max(props.rippleIntensity ?? 0, 0), 1);
  return {
    "--voice-ripple-boost": intensity.toFixed(3),
    "--voice-ripple-opacity": (0.18 + intensity * 0.12).toFixed(3),
    "--voice-ripple-duration": `${8600 - intensity * 700}ms`,
    "--voice-core-breathe-duration": `${4400 - intensity * 400}ms`,
    "--voice-core-scale": (1 + intensity * 0.08).toFixed(3),
  };
});
</script>

<template>
  <view
    class="cabin-voice-control-block"
    :class="{ 'cabin-voice-control-block--fade': transitioning }"
    :style="rippleStyle"
  >
    <view v-if="!recording && showPrimaryControls" class="cabin-voice-control-block__controls">
      <view class="cabin-voice-control-block__button-wrap">
        <image class="cabin-voice-control-block__halo" :src="CHAT_ASSETS.icons.voiceHalo" mode="aspectFit" />
        <image
          class="cabin-voice-control-block__purple-circle"
          :src="CHAT_ASSETS.icons.voicePurpleCircle"
          mode="aspectFit"
        />

        <view
          class="cabin-voice-control-block__trigger"
          hover-class="cabin-voice-control-block__trigger--hover"
          @click="emit('toggle')"
        >
          <image class="cabin-voice-control-block__mic" :src="CHAT_ASSETS.icons.voiceBody" mode="aspectFit" />
        </view>
      </view>

      <view
        v-if="showWriteEntry"
        class="cabin-voice-control-block__write-entry"
        hover-class="cabin-voice-control-block__write-entry--hover"
        @click="emit('write')"
      >
        <image class="cabin-voice-control-block__write-icon" :src="CHAT_ASSETS.icons.writeEntry" mode="aspectFit" />
      </view>
    </view>

    <view v-else class="cabin-voice-control-block__recording-stage">
      <view class="cabin-voice-control-block__water-ripple cabin-voice-control-block__water-ripple--a" />
      <view class="cabin-voice-control-block__water-ripple cabin-voice-control-block__water-ripple--b" />
      <view class="cabin-voice-control-block__water-ripple cabin-voice-control-block__water-ripple--c" />
      <image
        class="cabin-voice-control-block__ripple-outer"
        :src="CHAT_ASSETS.icons.voiceRippleOuter"
        mode="aspectFit"
      />
      <image
        class="cabin-voice-control-block__ripple-inner"
        :src="CHAT_ASSETS.icons.voiceRippleInner"
        mode="aspectFit"
      />
      <VoiceEndChatButton class="cabin-voice-control-block__stop-button" @click="emit('toggle')" />
    </view>

    <view v-if="showMeta" class="cabin-voice-control-block__status">
      <text class="cabin-voice-control-block__status-text">{{ liveStatusText }}</text>
      <text class="cabin-voice-control-block__duration">{{ durationText }}</text>
    </view>

    <view v-if="showActions" class="cabin-voice-control-block__actions">
      <view class="cabin-voice-control-block__action">
        <ChatOutlineButton :label="cancelLabel" @click="emit('cancel')" />
      </view>
      <view class="cabin-voice-control-block__action">
        <ChatOutlineButton :label="confirmLabel" :disabled="confirmDisabled" @click="emit('confirm')" />
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.cabin-voice-control-block {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30rpx;
  transition: opacity 220ms ease, transform 220ms ease;
}

.cabin-voice-control-block--fade {
  opacity: 0;
  transform: translateY(12rpx);
}

.cabin-voice-control-block__controls {
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 48rpx;
}

.cabin-voice-control-block__button-wrap {
  position: relative;
  width: 320rpx;
  height: 320rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cabin-voice-control-block__halo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.98;
}

.cabin-voice-control-block__purple-circle {
  position: absolute;
  left: 75rpx;
  top: 75rpx;
  width: 170rpx;
  height: 170rpx;
  opacity: 0.95;
}

.cabin-voice-control-block__trigger {
  position: relative;
  width: 170rpx;
  height: 170rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.cabin-voice-control-block__trigger--hover {
  opacity: 0.88;
  transform: scale(0.98);
}

.cabin-voice-control-block__mic {
  width: 56rpx;
  height: 56rpx;
}

.cabin-voice-control-block__write-entry {
  width: 56rpx;
  height: 56rpx;
  margin-bottom: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cabin-voice-control-block__write-entry--hover {
  opacity: 0.8;
  transform: translateY(2rpx);
}

.cabin-voice-control-block__write-icon {
  width: 56rpx;
  height: 56rpx;
  opacity: 0.92;
}

.cabin-voice-control-block__recording-stage {
  position: relative;
  width: 416rpx;
  height: 416rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cabin-voice-control-block__ripple-outer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.12;
}

.cabin-voice-control-block__ripple-inner {
  position: absolute;
  left: 112rpx;
  top: 112rpx;
  width: 192rpx;
  height: 192rpx;
  opacity: 0.76;
  animation: voice-ripple-breathe var(--voice-core-breathe-duration, 2800ms) ease-in-out infinite;
}

.cabin-voice-control-block__water-ripple {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 158rpx;
  height: 158rpx;
  border-radius: 50%;
  border: 0.8rpx solid rgba(227, 237, 255, var(--voice-ripple-opacity, 0.18));
  box-shadow: 0 0 10rpx rgba(214, 226, 255, 0.04);
  transform: translate(-50%, -50%) scale(0.34);
  opacity: 0;
}

.cabin-voice-control-block__water-ripple--a {
  animation: voice-water-ripple var(--voice-ripple-duration, 4200ms) cubic-bezier(0.16, 0.8, 0.24, 1) infinite;
}

.cabin-voice-control-block__water-ripple--b {
  animation: voice-water-ripple var(--voice-ripple-duration, 4200ms) cubic-bezier(0.16, 0.8, 0.24, 1) infinite calc(var(--voice-ripple-duration, 4200ms) / 3);
}

.cabin-voice-control-block__water-ripple--c {
  animation: voice-water-ripple var(--voice-ripple-duration, 4200ms) cubic-bezier(0.16, 0.8, 0.24, 1) infinite calc(var(--voice-ripple-duration, 4200ms) / 3 * 2);
}

.cabin-voice-control-block__stop-button {
  position: relative;
  z-index: 2;
}

.cabin-voice-control-block__status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.cabin-voice-control-block__status-text {
  color: $anima-text-main;
  font-size: 30rpx;
  line-height: 1.7;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
  text-align: center;
}

.cabin-voice-control-block__duration {
  color: $anima-text-dim;
  font-size: 24rpx;
  line-height: 1.5;
  letter-spacing: 1rpx;
  font-family: $anima-font-display;
}

.cabin-voice-control-block__actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22rpx;
}

.cabin-voice-control-block__action {
  width: 142rpx;
  height: 66rpx;
}

@keyframes voice-water-ripple {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.34);
  }

  10% {
    opacity: calc(var(--voice-ripple-opacity, 0.18) + 0.03);
  }

  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(calc(5.3 + var(--voice-ripple-boost, 0) * 0.35));
  }
}

@keyframes voice-ripple-breathe {
  0% {
    opacity: 0.68;
    transform: scale(calc(0.97 * var(--voice-core-scale, 1)));
  }

  50% {
    opacity: 0.9;
    transform: scale(calc(1.01 * var(--voice-core-scale, 1)));
  }

  100% {
    opacity: 0.68;
    transform: scale(calc(0.97 * var(--voice-core-scale, 1)));
  }
}

</style>

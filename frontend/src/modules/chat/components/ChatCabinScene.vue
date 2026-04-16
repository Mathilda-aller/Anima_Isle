<script setup lang="ts">
import { computed } from "vue";
import NightIp from "@/shared/components/NightIp.vue";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { SHARED_ASSETS } from "@/shared/assets";

const props = withDefaults(
  defineProps<{
    promptText?: string;
    showPrompt?: boolean;
    stageTop?: string;
    promptTop?: string;
    centerText?: string;
    showCenterText?: boolean;
    centerTop?: string;
    centerVariant?: "default" | "transcript";
    interactionTop?: string;
    interactionBottom?: string;
    interactionLeft?: string;
    interactionWidth?: string;
    showInteraction?: boolean;
    transitioning?: boolean;
  }>(),
  {
    promptText: "",
    showPrompt: true,
    stageTop: "16.25%",
    promptTop: "44.05%",
    centerText: "",
    showCenterText: false,
    centerTop: "43.25%",
    centerVariant: "default",
    interactionTop: "57.21%",
    interactionBottom: "",
    interactionLeft: "13.18%",
    interactionWidth: "78.36%",
    showInteraction: true,
    transitioning: false,
  },
);

const emit = defineEmits<{
  (e: "back"): void;
}>();

const promptLines = computed(() => props.promptText.split("\n").filter(Boolean));
const centerLines = computed(() => props.centerText.split("\n").filter(Boolean));
const interactionStyle = computed(() => ({
  top: props.interactionBottom ? undefined : props.interactionTop,
  bottom: props.interactionBottom || undefined,
  left: props.interactionLeft,
  width: props.interactionWidth,
}));
</script>

<template>
  <StageViewportShell>
    <view class="chat-cabin-scene__inner">
      <view class="chat-cabin-scene__artboard">
        <view class="chat-cabin-scene__topbar">
          <view class="chat-cabin-scene__back" hover-class="tap-hover" @click="emit('back')">
            <image class="chat-cabin-scene__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
          </view>
        </view>

        <view class="chat-cabin-scene__halo" />

        <slot name="stage-overlay" />

        <view class="chat-cabin-scene__stage" :style="{ top: stageTop }">
          <NightIp class="chat-cabin-scene__ip" />
        </view>

        <slot name="after-stage" />

        <view
          v-if="showPrompt && promptLines.length"
          class="chat-cabin-scene__copy"
          :class="{ 'chat-cabin-scene__fade': transitioning }"
          :style="{ top: promptTop }"
        >
          <text v-for="line in promptLines" :key="line" class="chat-cabin-scene__quote">{{ line }}</text>
        </view>

        <view
          v-if="showCenterText && centerLines.length"
          class="chat-cabin-scene__center-copy"
          :class="[
            { 'chat-cabin-scene__fade': transitioning },
            props.centerVariant === 'transcript' ? 'chat-cabin-scene__center-copy--transcript' : '',
          ]"
          :style="{ top: centerTop }"
        >
          <text
            v-for="line in centerLines"
            :key="line"
            class="chat-cabin-scene__center-quote"
            :class="props.centerVariant === 'transcript' ? 'chat-cabin-scene__center-quote--transcript' : ''"
          >{{ line }}</text>
        </view>

        <view
          v-if="showInteraction"
          class="chat-cabin-scene__interaction"
          :class="{ 'chat-cabin-scene__fade': transitioning }"
          :style="interactionStyle"
        >
          <slot name="interaction" />
        </view>

        <slot name="footer" />
      </view>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.chat-cabin-scene__inner {
  position: relative;
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1;
}

.chat-cabin-scene__artboard {
  position: relative;
  width: min(100%, calc((100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) * 402 / 874));
  max-width: 804rpx;
  aspect-ratio: 402 / 874;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
}

.chat-cabin-scene__topbar {
  position: absolute;
  top: 5.49%;
  left: 1%;
  width: 97.95%;
  padding: 0 4%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  z-index: 4;
}

.chat-cabin-scene__back {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-cabin-scene__back-icon {
  width: 48rpx;
  height: 48rpx;
}

.chat-cabin-scene__halo {
  position: absolute;
  left: 18.66%;
  top: 22.08%;
  width: 67.66%;
  height: 31.12%;
  border-radius: 9999rpx;
  background: $anima-glow-cabin-halo;
  filter: blur(64rpx);
  opacity: 0.95;
  z-index: 1;
  pointer-events: none;
}

.chat-cabin-scene__stage {
  position: absolute;
  left: 5.47%;
  width: 88.81%;
  z-index: 2;
}

.chat-cabin-scene__ip {
  position: relative;
  width: 100%;
}

.chat-cabin-scene__copy {
  position: absolute;
  left: 0.12%;
  width: 99.75%;
  text-align: center;
  z-index: 3;
}

.chat-cabin-scene__quote {
  display: block;
  color: $anima-text-main;
  font-size: 30rpx;
  line-height: 1.75;
  letter-spacing: 1rpx;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
  white-space: pre-wrap;
}

.chat-cabin-scene__center-copy {
  position: absolute;
  left: 0.37%;
  width: 99.25%;
  text-align: center;
  z-index: 3;
}

.chat-cabin-scene__center-copy--transcript {
  left: 19.9%;
  width: 60.2%;
}

.chat-cabin-scene__center-quote {
  display: block;
  color: $anima-text-main;
  font-size: 34rpx;
  line-height: 1.78;
  letter-spacing: 1.2rpx;
  text-shadow: 0 0 18rpx rgba(230, 248, 255, 0.36);
  font-family: $anima-font-display;
  white-space: pre-wrap;
}

.chat-cabin-scene__center-quote--transcript {
  color: rgba(224, 240, 255, 0.88);
  font-size: 24rpx;
  line-height: 1.85;
  letter-spacing: 1rpx;
  text-shadow: 0 0 10rpx rgba(230, 248, 255, 0.18);
}

.chat-cabin-scene__interaction {
  position: absolute;
  z-index: 4;
}

.chat-cabin-scene__fade {
  opacity: 0;
  transform: translateY(12rpx);
  transition: opacity 220ms ease, transform 220ms ease;
}

.tap-hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}
</style>

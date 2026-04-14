<script setup lang="ts">
import { computed } from "vue";
import { AUTH_ASSETS } from "@/modules/auth/assets";

const props = withDefaults(
  defineProps<{
    brand?: string;
    passengerLabel?: string;
    passengerLabelSub?: string;
    passengerValue?: string;
    travelLabel?: string;
    travelLabelSub?: string;
    residentTitle?: string;
    travelCount?: number;
    travelCountLabel?: string;
    verificationCode?: string;
  }>(),
  {
    brand: "言屿",
    passengerLabel: "PASSANGER",
    passengerLabelSub: "ID",
    passengerValue: "",
    travelLabel: "TRAVEL",
    travelLabelSub: "DAY",
    residentTitle: "拾光者",
    travelCount: 20,
    travelCountLabel: "",
    verificationCode: "",
  },
);

const displayResidentTitle = computed(() => props.passengerValue.trim() || props.residentTitle);

const displayTravelCount = computed(() => {
  if (props.travelCountLabel) return props.travelCountLabel;
  return `已旅行过${props.travelCount}座岛屿`;
});

const hasCustomResidentTitle = computed(() => Boolean(props.passengerValue.trim()));

const ticketMaskStyle = computed(() => ({
  maskImage: `url(${AUTH_ASSETS.residentTicket.shell})`,
  WebkitMaskImage: `url(${AUTH_ASSETS.residentTicket.shell})`,
}));
</script>

<template>
  <view class="resident-ticket-card">
    <view class="resident-ticket-card__glass-fill" :style="ticketMaskStyle"></view>
    <view class="resident-ticket-card__shell-wrap">
      <image class="resident-ticket-card__shell" :src="AUTH_ASSETS.residentTicket.shell" mode="scaleToFill" />
    </view>
    <view class="resident-ticket-card__content">
      <text class="resident-ticket-card__brand">{{ props.brand }}</text>

      <view class="resident-ticket-card__label resident-ticket-card__label--left">
        <text>{{ props.passengerLabel }}</text>
        <text>{{ props.passengerLabelSub }}</text>
      </view>
      <view class="resident-ticket-card__label resident-ticket-card__label--right">
        <text>{{ props.travelLabel }}</text>
        <text>{{ props.travelLabelSub }}</text>
      </view>

      <text
        class="resident-ticket-card__resident-title"
        :class="{ 'resident-ticket-card__resident-title--custom': hasCustomResidentTitle }"
      >
        {{ displayResidentTitle }}
      </text>
      <text class="resident-ticket-card__travel-count">{{ displayTravelCount }}</text>

      <image
        class="resident-ticket-card__divider resident-ticket-card__divider--vertical"
        :src="AUTH_ASSETS.residentTicket.dividerVertical"
        mode="scaleToFill"
      />
      <image
        class="resident-ticket-card__divider resident-ticket-card__divider--horizontal"
        :src="AUTH_ASSETS.residentTicket.dividerHorizontal"
        mode="scaleToFill"
      />

      <view class="resident-ticket-card__stamp">
        <text v-if="props.verificationCode" class="resident-ticket-card__stamp-text">{{ props.verificationCode }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.resident-ticket-card {
  position: relative;
  width: 100%;
  aspect-ratio: 295 / 548;
}

.resident-ticket-card__shell-wrap {
  position: absolute;
  inset: 0;
}

.resident-ticket-card__glass-fill {
  position: absolute;
  left: -10.85%;
  top: -5.11%;
  width: 121.7%;
  height: 111.68%;
  background: rgba(88, 101, 155, 0.26);
  mask-repeat: no-repeat;
  -webkit-mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-position: center;
  mask-size: 100% 100%;
  -webkit-mask-size: 100% 100%;
}

.resident-ticket-card__shell {
  position: absolute;
  left: -10.85%;
  top: -5.11%;
  width: 121.7%;
  height: 111.68%;
}

.resident-ticket-card__content {
  position: absolute;
  inset: 0;
  color: var(--anima-text-strong);
  font-family: var(--anima-font-display);
}

.resident-ticket-card__brand {
  position: absolute;
  left: 41.695%;
  top: 3.467%;
  width: 16.61%;
  text-align: center;
  font-size: 24px;
  line-height: 35px;
  opacity: 0.4;
  text-shadow: var(--anima-shadow-title);
}

.resident-ticket-card__label {
  position: absolute;
  top: 13.14%;
  display: flex;
  flex-direction: column;
  gap: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.92);
}

.resident-ticket-card__label text {
  font-size: 11px;
  line-height: 35px;
  letter-spacing: 0.8rpx;
}

.resident-ticket-card__label--left {
  left: 11.864%;
  width: 27.458%;
}

.resident-ticket-card__label--right {
  left: 60.678%;
  width: 25.763%;
}

.resident-ticket-card__resident-title,
.resident-ticket-card__travel-count {
  position: absolute;
  top: 27.007%;
  height: 37.02%;
  text-align: center;
  font-size: 20px;
  line-height: 20px;
  letter-spacing: 0.8rpx;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  white-space: nowrap;
}

.resident-ticket-card__resident-title {
  left: 19.661%;
  width: 11.864%;
}

.resident-ticket-card__resident-title--custom {
  font-size: 15px;
  line-height: 15px;
  letter-spacing: 0;
}

.resident-ticket-card__travel-count {
  left: 67.458%;
  width: 11.864%;
}

.resident-ticket-card__divider {
  position: absolute;
}

.resident-ticket-card__divider--vertical {
  left: 50.17%;
  top: 22.26%;
  width: 2rpx;
  height: 39.96%;
  opacity: 0.68;
}

.resident-ticket-card__divider--horizontal {
  left: 10.17%;
  top: 65.51%;
  width: 80%;
  height: 4rpx;
  opacity: 0.68;
}

.resident-ticket-card__stamp {
  position: absolute;
  left: 37.29%;
  top: 77.92%;
  width: 25.42%;
  aspect-ratio: 1 / 1;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.17);
  display: flex;
  align-items: center;
  justify-content: center;
}

.resident-ticket-card__stamp-text {
  width: 76%;
  text-align: center;
  font-size: 14rpx;
  line-height: 1.2;
  color: rgba(255, 255, 255, 0.72);
  word-break: break-all;
}
</style>

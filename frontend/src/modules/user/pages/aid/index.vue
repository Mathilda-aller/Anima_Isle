<script setup lang="ts">
import { computed } from "vue";
import { USER_ASSETS } from "@/modules/user/assets";
import { ROUTES } from "@/shared/constants/routes";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";

interface SupportLine {
  id: string;
  label: string;
  phone: string;
}

interface AidPageContent {
  headline: string;
  primaryActionLabel: string;
  ambientCaption: string;
  supportLines: SupportLine[];
}

const aidPageContent = computed<AidPageContent>(() => ({
  headline: "这里的潮汐，会抱住所有的疲惫。",
  primaryActionLabel: "连接专业倾听者",
  ambientCaption: "试着闭上眼，听一分钟海浪。",
  supportLines: [
    { id: "national", label: "全国心理援助热线", phone: "12356" },
    { id: "beijing", label: "北京心理援助热线", phone: "010-88585821" },
    { id: "shanghai", label: "上海心理援助热线", phone: "021-962525" },
    { id: "lifeline", label: "生命热线", phone: "400-161-9995" },
  ],
}));

function backToChat() {
  uni.reLaunch({ url: ROUTES.CHAT_HOME });
}

function callPrimarySupport() {
  const primary = aidPageContent.value.supportLines[0]?.phone;
  if (!primary) return;

  uni.makePhoneCall({
    phoneNumber: primary,
    fail: () => {
      uni.showToast({ title: "当前设备暂不支持拨号", icon: "none" });
    },
  });
}

function callSupportLine(phone: string) {
  if (!phone) return;

  uni.makePhoneCall({
    phoneNumber: phone,
    fail: () => {
      uni.showToast({ title: "当前设备暂不支持拨号", icon: "none" });
    },
  });
}
</script>

<template>
  <StageViewportShell>
    <view class="aid-page__inner">
      <view class="aid-page__artboard">
        <view class="aid-page__glow aid-page__glow--top" />
        <view class="aid-page__glow aid-page__glow--bottom" />

        <view class="aid-page__topbar">
          <view class="aid-page__back" hover-class="tap-hover" @click="backToChat">
            <image class="aid-page__back-line" :src="USER_ASSETS.icons.aidCloseA" mode="aspectFit" />
            <image class="aid-page__back-line" :src="USER_ASSETS.icons.aidCloseB" mode="aspectFit" />
          </view>
        </view>

        <text class="aid-page__headline">{{ aidPageContent.headline }}</text>

        <view class="aid-page__panel">
          <view class="aid-page__panel-button" hover-class="aid-page__panel-button--hover" @click="callPrimarySupport">
            <view class="aid-page__panel-button-glow" />
            <text class="aid-page__panel-button-text">{{ aidPageContent.primaryActionLabel }}</text>
          </view>

          <view class="aid-page__line-list">
            <view
              v-for="item in aidPageContent.supportLines"
              :key="item.id"
              class="aid-page__line-card"
              hover-class="aid-page__line-card--hover"
              @click="callSupportLine(item.phone)"
            >
              <text class="aid-page__line-label">{{ item.label }}</text>
              <text class="aid-page__line-phone">{{ item.phone }}</text>
            </view>
          </view>
        </view>

        <view class="aid-page__meditation">
          <view class="aid-page__ring aid-page__ring--outer" />
          <view class="aid-page__ring aid-page__ring--middle" />
          <view class="aid-page__ring aid-page__ring--inner" />
        </view>

        <text class="aid-page__footer-copy">{{ aidPageContent.ambientCaption }}</text>
      </view>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.aid-page__inner {
  position: relative;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: stretch;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 1;
}

.aid-page__artboard {
  position: relative;
  width: min(100%, calc((100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) * 402 / 874));
  max-width: 804rpx;
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  aspect-ratio: 402 / 874;
  overflow: hidden;
}

.aid-page__glow {
  position: absolute;
  filter: blur(64rpx);
  pointer-events: none;
}

.aid-page__glow--top {
  left: 50%;
  top: 11.1%;
  width: 108.95%;
  height: 24.49%;
  transform: translateX(-50%);
  background: radial-gradient(circle at 50% 50%, rgba(95, 200, 224, 0.28) 0%, rgba(95, 200, 224, 0.09) 36%, rgba(95, 200, 224, 0) 74%);
  opacity: 0.88;
}

.aid-page__glow--bottom {
  left: 50%;
  top: 61.21%;
  width: 82.09%;
  height: 20.59%;
  transform: translateX(-50%);
  background: radial-gradient(circle at 50% 50%, rgba(255, 244, 188, 0.18) 0%, rgba(255, 244, 188, 0.05) 42%, rgba(255, 244, 188, 0) 80%);
  opacity: 0.94;
}

.aid-page__topbar {
  position: absolute;
  top: 5.49%;
  left: 0;
  width: 100%;
  padding: 0 6.72%;
  z-index: 4;
}

.aid-page__back {
  position: relative;
  width: 11.94%;
  max-width: 48rpx;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 180ms ease, transform 180ms ease;
}

.aid-page__back-line {
  position: absolute;
  width: 58.34%;
  height: 58.34%;
}

.aid-page__headline {
  position: absolute;
  top: 20.25%;
  left: 50%;
  width: 71.4%;
  transform: translateX(-50%);
  color: #c5d3e0;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 80rpx;
  letter-spacing: 2.56rpx;
  text-align: center;
}

.aid-page__panel {
  position: absolute;
  top: 33.98%;
  left: 50%;
  width: 70.9%;
  height: 45.65%;
  transform: translateX(-50%);
  border: 1.5rpx solid rgba(192, 201, 215, 0.18);
  border-radius: 48rpx;
  background: linear-gradient(180deg, rgba(182, 198, 219, 0.03) 0%, rgba(24, 29, 42, 0.18) 100%);
  backdrop-filter: blur(10rpx);
  box-shadow:
    inset 0 0 0 1rpx rgba(255, 255, 255, 0.08),
    0 24rpx 60rpx rgba(0, 0, 0, 0.12);
}

.aid-page__panel-button {
  position: absolute;
  top: 7.77%;
  left: 50%;
  width: 78.25%;
  height: 11.28%;
  transform: translateX(-50%);
  overflow: hidden;
  border-radius: 32rpx;
  background: linear-gradient(168.52deg, rgba(230, 240, 250, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  box-shadow:
    0 0 60rpx rgba(230, 240, 250, 0.3),
    0 8rpx 32rpx rgba(0, 0, 0, 0.2);
}

.aid-page__panel-button-glow {
  position: absolute;
  left: -5.83%;
  top: -28.89%;
  width: 104.04%;
  height: 148.89%;
  opacity: 0.5;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.6) 0%, rgba(191, 191, 191, 0.45) 17.5%, rgba(0, 0, 0, 0) 70%);
}

.aid-page__panel-button-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1e293b;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 54rpx;
  letter-spacing: 1.28rpx;
}

.aid-page__line-list {
  position: absolute;
  top: 26.56%;
  left: 50%;
  width: 81.06%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 3.01%;
}

.aid-page__line-card {
  height: 14.03%;
  min-height: 112rpx;
  padding: 0 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1.5rpx solid rgba(148, 163, 184, 0.15);
  border-radius: 28rpx;
  background: rgba(51, 65, 85, 0.16);
  transition: opacity 180ms ease, transform 180ms ease;
}

.aid-page__line-label {
  max-width: 48%;
  color: #94a3b8;
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 40rpx;
}

.aid-page__line-phone {
  color: #cbd5e1;
  font-family: $anima-font-display;
  font-size: 24rpx;
  line-height: 48rpx;
  letter-spacing: 1.44rpx;
  text-align: right;
}

.aid-page__meditation {
  position: absolute;
  top: 66.25%;
  left: 50%;
  width: 27.87%;
  aspect-ratio: 1;
  transform: translateX(-50%);
}

.aid-page__ring {
  position: absolute;
  border-radius: 999rpx;
}

.aid-page__ring--outer {
  inset: 0;
  border: 1.5rpx solid rgba(255, 253, 244, 0.5);
  opacity: 0.47;
  box-shadow: 0 0 40rpx rgba(255, 240, 173, 0.25);
}

.aid-page__ring--middle {
  inset: 28rpx;
  border: 1.5rpx solid rgba(255, 255, 255, 0.44);
  opacity: 0.6;
  box-shadow: 0 0 40rpx rgba(255, 248, 123, 0.2);
}

.aid-page__ring--inner {
  inset: 60rpx;
  border: 3rpx solid rgba(254, 236, 194, 0.19);
  box-shadow:
    0 0 60rpx rgba(255, 255, 255, 0.6),
    inset 0 0 40rpx rgba(185, 253, 237, 0.2);
  background: rgba(255, 240, 173, 0.25);
}

.aid-page__footer-copy {
  position: absolute;
  left: 50%;
  top: 85.13%;
  width: 73.89%;
  transform: translateX(-50%);
  color: #94a3b8;
  font-family: $anima-font-display;
  font-size: 32rpx;
  line-height: 52rpx;
  letter-spacing: 1.6rpx;
  text-align: center;
}

.aid-page__panel-button--hover,
.tap-hover,
.aid-page__line-card--hover {
  opacity: 0.84;
}

.aid-page__panel-button--hover {
  transform: translateX(-50%) translateY(-2rpx);
}

.aid-page__back.tap-hover {
  transform: translateY(-2rpx);
}

@media screen and (min-width: 768px) {
  .aid-page__artboard {
    width: min(calc((100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) * 402 / 874), 804rpx);
  }
}
</style>

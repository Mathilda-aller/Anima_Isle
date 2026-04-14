<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import ResidentTicketCard from "@/modules/auth/components/ResidentTicketCard.vue";
import { AUTH_ASSETS } from "@/modules/auth/assets";
import { useAuthStore } from "@/modules/auth/store/auth";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { ROUTES } from "@/shared/constants/routes";
import { SHARED_ASSETS } from "@/shared/assets";
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";
import { navigateToWithFeedback, toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const ticketStore = useTicketStore();
const showCommunityModal = ref(false);
const loading = ref(false);

const latestTicket = computed(() => ticketStore.timeline[0] ?? null);
const residentPassengerId = computed(() => authStore.userInfo?.nickname?.trim() ?? "");
const residentTravelCount = computed(() => authStore.userInfo?.travel_count ?? ticketStore.timeline.length);
const residentVerificationCode = computed(() => latestTicket.value?.ticket_uid.slice(-6).toUpperCase() ?? "");
const residentTravelLabel = computed(() => {
  if (residentTravelCount.value <= 0) {
    return "尚未启航";
  }

  return `已完成${residentTravelCount.value}次航行`;
});
const ticketHint = computed(() => {
  if (loading.value) {
    return "正在同步你的屿民船票...";
  }

  if (latestTicket.value) {
    return "点击查看你的屿民船票";
  }

  return "完成一次情绪航行后，这里会生成你的专属屿民船票";
});

onShow(async () => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  loading.value = true;
  try {
    await Promise.all([authStore.fetchMeProfile(), ticketStore.refreshList()]);
  } catch {
    // Keep current local state when refresh fails.
  } finally {
    loading.value = false;
  }
});

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack();
    return;
  }
  uni.reLaunch({ url: ROUTES.CHAT_HOME });
}

function openIdentity() {
  const latestTicketUid = latestTicket.value?.ticket_uid;
  const query = latestTicketUid ? `?ticket_uid=${encodeURIComponent(latestTicketUid)}` : "";
  navigateToWithFeedback(`${ROUTES.AUTH_RESIDENT_TICKET}${query}`);
}

function openCommunityModal() {
  showCommunityModal.value = true;
}

function closeCommunityModal() {
  showCommunityModal.value = false;
}
</script>

<template>
  <view class="resident-page">
    <view class="resident-page__shell">
      <view class="resident-page__main" :class="{ 'resident-page__main--blurred': showCommunityModal }">
        <DarkBackgroundLayer />

        <view class="resident-page__scene-shell">
          <image class="resident-page__scene" :src="AUTH_ASSETS.illustrations.residentScene" mode="aspectFill" />
          <view class="resident-page__scene-mask"></view>
        </view>
        <view class="resident-page__scene-transition"></view>

        <view class="resident-page__canvas">
          <view class="resident-page__topbar">
            <view class="resident-page__back" hover-class="tap-hover" @click="goBack">
              <image class="resident-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
            </view>
            <text class="resident-page__topbar-title">成为屿民</text>
            <view class="resident-page__topbar-spacer"></view>
          </view>

          <view class="resident-page__hero">
            <text class="resident-page__hero-title">成为屿民</text>
            <view class="resident-page__hero-copy">
              <text class="resident-page__hero-copy-line">没有人是一座孤岛，你的情绪值得被看见。</text>
              <text class="resident-page__hero-copy-line">加入屿民社群，参与我们的情绪疗愈活动。</text>
            </view>
          </view>

          <view class="resident-page__panel">
            <text class="resident-page__panel-title">我的船票</text>

            <view class="resident-page__ticket-shell">
              <view class="resident-page__card-wrap" hover-class="card-hover" @click="openIdentity">
                <view class="resident-page__card-rotation">
                  <ResidentTicketCard
                    class="resident-page__card-preview"
                    :passenger-value="residentPassengerId"
                    :travel-count="residentTravelCount"
                    :travel-count-label="residentTravelLabel"
                    :verification-code="residentVerificationCode"
                  />
                </view>
              </view>
            </view>

            <text class="resident-page__ticket-hint">{{ ticketHint }}</text>

            <view class="resident-page__faq">
              <text class="resident-page__faq-line">Q.我的船票有什么用？</text>
              <text class="resident-page__faq-line">A.船票是参与线上线下活动的唯一身份识别凭证。</text>
            </view>
          </view>

          <button class="resident-page__cta" hover-class="button-hover" @click="openCommunityModal">加入社群</button>
        </view>
      </view>

      <view v-if="showCommunityModal" class="resident-page__overlay">
        <view class="resident-page__overlay-cover"></view>
        <view class="resident-page__overlay-inner">
          <view class="resident-page__community-close" hover-class="tap-hover" @click="closeCommunityModal">
            <image class="resident-page__community-close-line" :src="AUTH_ASSETS.resident.communityCloseA" mode="aspectFit" />
            <image class="resident-page__community-close-line" :src="AUTH_ASSETS.resident.communityCloseB" mode="aspectFit" />
          </view>
          <view class="resident-page__community-slot">
            <text class="resident-page__community-placeholder">二维码留白区域</text>
          </view>
          <text class="resident-page__community-tip">在微信长按二维码加入社群</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.resident-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--anima-night-gradient);
}

.resident-page__shell {
  position: relative;
  width: 100%;
  min-height: 100vh;
  margin: 0 auto;
  overflow: hidden;
  background: var(--anima-night-gradient);
  font-family: var(--anima-font-display);
}

.resident-page__main {
  position: relative;
  min-height: 100vh;
  transition: filter 0.24s ease, transform 0.24s ease;
}

.resident-page__main--blurred {
  filter: blur(18rpx);
  transform: scale(0.992);
}

.resident-page__scene-shell {
  position: absolute;
  top: -9px;
  left: 0;
  width: 100%;
  height: 632px;
  overflow: hidden;
  pointer-events: none;
}

.resident-page__scene {
  position: absolute;
  top: -0.02%;
  left: 0;
  width: 100%;
  height: 113.64%;
  opacity: 0.94;
}

.resident-page__scene-mask {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(3, 13, 32, 0.04) 0%, rgba(3, 13, 32, 0.12) 42%, rgba(3, 13, 32, 0.46) 100%),
    radial-gradient(circle at 50% 82%, rgba(126, 218, 255, 0.16) 0%, rgba(126, 218, 255, 0) 34%);
}

.resident-page__scene-transition {
  position: absolute;
  left: 0;
  top: 528px;
  width: 100%;
  height: 96px;
  background:
    radial-gradient(circle at 50% 0, rgba(108, 130, 225, 0.18) 0%, rgba(108, 130, 225, 0) 48%),
    linear-gradient(180deg, rgba(108, 130, 225, 0) 0%, rgba(78, 94, 162, 0.62) 59.135%, #354278 100%);
  opacity: 0.96;
  filter: blur(2px);
  z-index: 0;
}

.resident-page__canvas {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: max(874px, calc(100vh - env(safe-area-inset-bottom)));
  flex-direction: column;
  align-items: center;
  padding-bottom: calc(46px + env(safe-area-inset-bottom));
}

.resident-page__topbar {
  position: relative;
  z-index: 2;
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  padding: calc(44px + env(safe-area-inset-top)) 16px 0;
}

.resident-page__back {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resident-page__topbar-spacer {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.resident-page__back-icon {
  width: 24px;
  height: 24px;
}

.resident-page__topbar-title {
  color: var(--anima-text-main);
  font-size: 24px;
  line-height: 35px;
  letter-spacing: 0.5px;
  text-align: center;
  text-shadow: var(--anima-shadow-title);
}

.resident-page__hero {
  width: 100%;
  margin-top: 41px;
  padding: 0 24px;
}

.resident-page__hero-title {
  color: var(--anima-text-strong);
  font-size: 24px;
  line-height: 28px;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.resident-page__hero-copy {
  width: 100%;
  max-width: 313px;
  margin-top: 21px;
  display: flex;
  flex-direction: column;
  gap: 0;
  color: var(--anima-text-strong);
  font-size: 16px;
  line-height: 28px;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.resident-page__hero-copy-line {
  display: block;
  max-width: 100%;
  white-space: normal;
}

.resident-page__panel {
  width: 89.05%;
  max-width: 358px;
  min-height: 218px;
  margin-top: 295px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  overflow: hidden;
  border: 1px solid rgba(236, 247, 255, 0.16);
  border-radius: 34.844px;
  background:
    radial-gradient(circle at 0 18%, rgba(18, 211, 255, 0.07) 0%, rgba(18, 211, 255, 0) 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.02) 100%),
    rgba(7, 17, 42, 0.22);
  box-shadow: var(--anima-resident-shadow);
  backdrop-filter: blur(24rpx);
  padding: 17px 33px 12px;
}

.resident-page__panel-title {
  width: 100%;
  color: var(--anima-text-strong);
  font-size: 16px;
  line-height: 28px;
  text-align: center;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

.resident-page__ticket-shell {
  display: flex;
  width: 100%;
  justify-content: center;
  margin-top: 14px;
}

.resident-page__card-wrap {
  width: 156.04px;
  height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}

.resident-page__card-rotation {
  width: 84px;
  height: 156.04px;
  transform: rotate(-90deg) scale(0.2847);
  transform-origin: center;
}

.resident-page__card-preview {
  width: 295px;
}

.resident-page__ticket-hint {
  width: 100%;
  color: rgba(255, 255, 255, 0.72);
  font-size: 10px;
  line-height: 18px;
  letter-spacing: 0.5px;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.24);
  white-space: normal;
}

.resident-page__faq {
  display: flex;
  width: 100%;
  flex-direction: column;
}

.resident-page__faq-line {
  color: var(--anima-text-strong);
  font-size: 10px;
  line-height: 20px;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.37);
  white-space: normal;
}

.resident-page__cta {
  position: relative;
  width: 104px;
  height: 33px;
  margin-top: 32px;
  padding: 0;
  line-height: 33px;
  border: none;
  border-radius: 15px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.015) 100%),
    rgba(0, 0, 0, 0);
  color: var(--anima-text-strong);
  font-size: 16px;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.48),
    0 0 18px rgba(184, 213, 255, 0.12);
}

.resident-page__cta::after {
  border: none;
}

.resident-page__cta::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(180deg, rgba(233, 243, 255, 0.72) 0%, rgba(170, 193, 238, 0.22) 100%);
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.tap-hover,
.card-hover,
.button-hover {
  opacity: 0.88;
}

.card-hover {
  transform: translateY(-2rpx);
}

.resident-page__overlay {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  overflow: hidden;
}

.resident-page__overlay-cover {
  position: absolute;
  inset: 0;
  background: rgba(13, 19, 35, 0.5);
  backdrop-filter: blur(4rpx);
}

.resident-page__overlay-inner {
  position: relative;
  z-index: 2;
  display: flex;
  width: 100%;
  min-height: 100vh;
  flex-direction: column;
  align-items: center;
  padding: calc(48px + env(safe-area-inset-top)) 16px calc(54px + env(safe-area-inset-bottom));
}

.resident-page__community-close {
  align-self: flex-start;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
}

.resident-page__community-close-line {
  grid-area: 1 / 1;
  width: 24px;
  height: 24px;
}

.resident-page__community-slot {
  width: 202px;
  height: 202px;
  margin-top: 254px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.8);
}

.resident-page__community-placeholder {
  color: rgba(44, 65, 122, 0.42);
  font-size: 22rpx;
  line-height: 1.4;
  letter-spacing: 1rpx;
}

.resident-page__community-tip {
  margin-top: 39px;
  color: var(--anima-text-strong);
  font-size: 16px;
  line-height: 28px;
  letter-spacing: 0.5px;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);
}

@media screen and (min-width: 768px) {
  .resident-page__shell {
    max-width: 402px;
  }
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import ResidentTicketCard from "@/modules/auth/components/ResidentTicketCard.vue";
import { useAuthStore } from "@/modules/auth/store/auth";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { TICKET_ASSETS } from "@/modules/ticket/assets";
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";
import { ROUTES } from "@/shared/constants/routes";
import { reLaunchWithFeedback, toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const ticketStore = useTicketStore();
const ticketUid = ref("");
const loading = ref(false);

const residentPassengerId = computed(() => authStore.userInfo?.nickname?.trim() ?? "");
const residentTravelCount = computed(() => authStore.userInfo?.travel_count ?? ticketStore.timeline.length);
const ticketDetail = computed(() => {
  if (!ticketUid.value) {
    return null;
  }

  return ticketStore.detailMap[ticketUid.value] ?? null;
});
const residentVerificationCode = computed(() => {
  const source = ticketDetail.value?.ticket_uid ?? ticketUid.value;
  return source ? source.slice(-6).toUpperCase() : "";
});
const residentTravelLabel = computed(() => {
  if (residentTravelCount.value <= 0) {
    return "尚未启航";
  }

  return `已旅行过${residentTravelCount.value}座岛屿`;
});
const residentHint = computed(() => {
  if (loading.value) {
    return "正在同步屿民信息...";
  }

  if (ticketDetail.value) {
    return "这张船票会作为你参与活动的身份凭证";
  }

  return "完成一次情绪航行后，这里会展示你的专属屿民船票";
});

onLoad((query) => {
  if (typeof query?.ticket_uid === "string") {
    ticketUid.value = query.ticket_uid;
  }
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

    if (!ticketUid.value && ticketStore.timeline.length) {
      ticketUid.value = ticketStore.timeline[0].ticket_uid;
    }

    if (ticketUid.value) {
      await ticketStore.fetchDetail(ticketUid.value);
    }
  } catch {
    // Keep fallback values from current local state when refresh fails.
  } finally {
    loading.value = false;
  }
});

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  reLaunchWithFeedback(ROUTES.AUTH_RESIDENT);
}

function shareTicket() {
  uni.showToast({ title: "分享功能即将开放", icon: "none" });
}
</script>

<template>
  <view class="resident-ticket-page">
    <view class="resident-ticket-page__shell">
      <DarkBackgroundLayer />
      <view class="resident-ticket-page__glow"></view>

      <view class="resident-ticket-page__header">
        <view class="resident-ticket-page__header-spacer"></view>
        <text class="resident-ticket-page__title">我的船票</text>
        <view class="resident-ticket-page__share" hover-class="tap-hover" @click="shareTicket">
          <image class="resident-ticket-page__share-icon" :src="TICKET_ASSETS.icons.share" mode="aspectFit" />
        </view>
      </view>

      <view class="resident-ticket-page__stage">
        <view class="resident-ticket-page__ticket" hover-class="tap-hover" @click="goBack">
          <ResidentTicketCard
            :passenger-value="residentPassengerId"
            :travel-count="residentTravelCount"
            :travel-count-label="residentTravelLabel"
            :verification-code="residentVerificationCode"
          />
        </view>
        <text class="resident-ticket-page__hint">{{ residentHint }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.resident-ticket-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--anima-night-gradient);
}

.resident-ticket-page__shell {
  position: relative;
  width: 100%;
  max-width: 402px;
  min-height: 100vh;
  margin: 0 auto;
  overflow: hidden;
  background: var(--anima-night-gradient);
  font-family: var(--anima-font-display);
}

.resident-ticket-page__glow {
  position: absolute;
  left: 49%;
  top: 2.63%;
  width: 67.66%;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(116, 212, 234, 0.54) 0%,
    rgba(90, 166, 183, 0.705) 12.74%,
    rgba(65, 120, 132, 0.87) 25.481%,
    rgba(65, 120, 132, 0) 68%
  );
  filter: blur(64rpx);
  pointer-events: none;
}

.resident-ticket-page__header {
  position: relative;
  z-index: 2;
  padding: calc(88rpx + env(safe-area-inset-top)) 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.resident-ticket-page__title {
  color: var(--anima-text-main);
  font-family: var(--anima-font-display);
  font-size: 48rpx;
  line-height: 70rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: var(--anima-shadow-title);
}

.resident-ticket-page__header-spacer,
.resident-ticket-page__share {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resident-ticket-page__share-icon {
  width: 48rpx;
  height: 48rpx;
}

.resident-ticket-page__stage {
  position: relative;
  z-index: 2;
  min-height: calc(100vh - 120rpx - env(safe-area-inset-top));
  display: flex;
  justify-content: center;
  padding-top: 160rpx;
}

.resident-ticket-page__ticket {
  width: 73.38%;
  max-width: 295px;
}

.resident-ticket-page__hint {
  margin-top: 36rpx;
  width: 72%;
  color: rgba(255, 255, 255, 0.74);
  font-size: 24rpx;
  line-height: 38rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.24);
}

.tap-hover {
  opacity: 0.88;
}
</style>

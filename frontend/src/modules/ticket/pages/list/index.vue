<script setup lang="ts">
import { computed } from "vue";
import { onReachBottom, onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import TicketTimelineCard from "@/modules/ticket/components/TicketTimelineCard.vue";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { SHARED_ASSETS } from "@/shared/assets";
import { ROUTES } from "@/shared/constants/routes";
import StageViewportShell from "@/shared/components/StageViewportShell.vue";
import { toLogin } from "@/shared/utils/navigation";

const authStore = useAuthStore();
const ticketStore = useTicketStore();

const hasTimeline = computed(() => ticketStore.timeline.length > 0);

onShow(async () => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }
  await ticketStore.refreshList();
});

onReachBottom(async () => {
  await ticketStore.fetchList();
});

function openViewer(ticketUid: string) {
  uni.navigateTo({
    url: `${ROUTES.TICKET_VIEWER}?ticket_uid=${encodeURIComponent(ticketUid)}`,
  });
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  uni.reLaunch({ url: ROUTES.CHAT_HOME });
}
</script>

<template>
  <StageViewportShell>
    <view class="ticket-list-page__inner">
      <view class="ticket-list-page__topbar">
        <view class="ticket-list-page__back" hover-class="tap-hover" @click="goBack">
          <image class="ticket-list-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
        </view>
        <text class="ticket-list-page__title">记忆航线</text>
        <view class="ticket-list-page__topbar-spacer"></view>
      </view>

      <view v-if="hasTimeline" class="ticket-list-page__timeline">
        <TicketTimelineCard
          v-for="(item, index) in ticketStore.timeline"
          :key="item.ticket_uid"
          :item="item"
          :align="index % 2 === 0 ? 'left' : 'right'"
          :show-connector="index !== ticketStore.timeline.length - 1"
          @open="openViewer"
        />
      </view>

      <view v-else-if="!ticketStore.loading" class="ticket-list-page__state">
        <text class="ticket-list-page__state-text">还没有船票，先去聊天生成一张吧。</text>
      </view>

      <view v-if="ticketStore.loading" class="ticket-list-page__loading">
        <text class="ticket-list-page__loading-text">潮汐正在捞取你的航线...</text>
      </view>
    </view>
  </StageViewportShell>
</template>

<style scoped lang="scss">
.ticket-list-page__inner {
  position: relative;
  min-height: 100vh;
  width: min(100%, 804rpx);
  margin: 0 auto;
  padding: 0 24rpx calc(40rpx + env(safe-area-inset-bottom));
  z-index: 1;
}

.ticket-list-page__topbar {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(88rpx + env(safe-area-inset-top)) 32rpx 0;
}

.ticket-list-page__back,
.ticket-list-page__topbar-spacer {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
}

.ticket-list-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 180ms ease, transform 180ms ease;
}

.ticket-list-page__back-icon {
  width: 48rpx;
  height: 48rpx;
}

.ticket-list-page__title {
  color: var(--anima-text-main);
  font-family: var(--anima-font-display);
  font-size: 48rpx;
  line-height: 70rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: var(--anima-shadow-title);
}

.ticket-list-page__timeline {
  margin-top: 72rpx;
  width: 647rpx;
  margin-left: auto;
  margin-right: auto;
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.ticket-list-page__state,
.ticket-list-page__loading {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}

.ticket-list-page__state-text,
.ticket-list-page__loading-text {
  color: var(--anima-text-dim);
  font-family: var(--anima-font-display);
  font-size: 28rpx;
  line-height: 48rpx;
  text-align: center;
}

.tap-hover {
  opacity: 0.82;
  transform: translateY(-2rpx);
}

@media screen and (max-width: 420px) {
  .ticket-list-page__inner {
    width: 100%;
    padding-left: 16rpx;
    padding-right: 16rpx;
  }

  .ticket-list-page__timeline {
    width: 100%;
  }
}
</style>

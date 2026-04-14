<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import ResidentTicketCard from "@/modules/auth/components/ResidentTicketCard.vue";
import { useAuthStore } from "@/modules/auth/store/auth";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { TICKET_ASSETS } from "@/modules/ticket/assets";
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";
import { toLogin } from "@/shared/utils/navigation";

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

  return `已完成${residentTravelCount.value}次航行`;
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

function shareTicket() {
  uni.showToast({ title: "分享功能即将开放", icon: "none" });
}
</script>

<template>
  <view class="resident-ticket-page">
    <view class="resident-ticket-page__shell">
      <DarkBackgroundLayer :textureOpacity="0.2" />
      <view class="resident-ticket-page__glow"></view>

      <!-- Header: title LEFT, share icon RIGHT — matches Figma node 1:413 -->
      <view class="resident-ticket-page__header">
        <text class="resident-ticket-page__title">我的船票</text>
        <view class="resident-ticket-page__share" hover-class="tap-hover" @click="shareTicket">
          <image class="resident-ticket-page__share-icon" :src="TICKET_ASSETS.icons.share" mode="aspectFit" />
        </view>
      </view>

      <!-- Stage: ticket card at 102px below header, matching Figma card top at 198px -->
      <view class="resident-ticket-page__stage">
        <view class="resident-ticket-page__ticket">
          <ResidentTicketCard
            :passenger-value="residentPassengerId"
            :travel-count="residentTravelCount"
            :travel-count-label="residentTravelLabel"
            :verification-code="residentVerificationCode"
          />
        </view>
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

/* Glow: blurred cyan radial at top-right — Figma: left 197/402=49%, top 23/874=2.63%, size 272/402=67.66% */
.resident-ticket-page__glow {
  position: absolute;
  left: 49%;
  top: 2.63%;
  width: 67.66%;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  background: var(--anima-glow-ticket);
  filter: blur(64rpx);
  pointer-events: none;
}

/* Header: height 56px, top 40px, px 16px — matches Figma node 1:413 (h-[55.991px] top-[40px] px-[16px]) */
.resident-ticket-page__header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(40px + env(safe-area-inset-top)) 16px 0;
  height: calc(96px + env(safe-area-inset-top));
}

/* Title: left-aligned, 24px/35px — matches Figma node 1:414 */
.resident-ticket-page__title {
  color: var(--anima-text-main);
  font-family: var(--anima-font-display);
  font-size: 24px;
  line-height: 35px;
  letter-spacing: 0.5px;
  text-shadow: var(--anima-shadow-title);
}

/* Share icon: 24px — matches Figma node 1:415 (size-[23.993px]) */
.resident-ticket-page__share {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resident-ticket-page__share-icon {
  width: 24px;
  height: 24px;
}

/* Stage: flex column, 102px top padding places card at ~198px from page top matching Figma */
.resident-ticket-page__stage {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 102px;
  padding-bottom: 48px;
}

/* Card: 295px wide (73.38% of 402px), portrait orientation — matches Figma node 1:423 (w-[295px] h-[548px]) */
.resident-ticket-page__ticket {
  width: 73.38%;
  max-width: 295px;
}

.tap-hover {
  opacity: 0.88;
}
</style>

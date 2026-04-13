<script setup lang="ts">
import { computed } from "vue";
import { TICKET_ASSETS } from "@/modules/ticket/assets";
import type { TicketDTO } from "@/modules/ticket/types/ticket";

const props = withDefaults(
  defineProps<{
    item: TicketDTO;
    align?: "left" | "right";
  }>(),
  {
    align: "left",
  },
);

const emit = defineEmits<{
  (e: "open", ticketUid: string): void;
}>();

const poemLines = computed(() =>
  (props.item.poem_content ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 3),
);

const monthDayLabel = computed(() => {
  const date = new Date(props.item.created_at);
  if (Number.isNaN(date.getTime())) return "";

  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${monthNames[date.getMonth()]} ${date.getDate()}`;
});
</script>

<template>
  <view class="ticket-timeline-card" :class="`ticket-timeline-card--${align}`">
    <view
      class="ticket-timeline-card__card"
      hover-class="ticket-timeline-card__card--hover"
      @click="emit('open', item.ticket_uid)"
    >
      <image class="ticket-timeline-card__image" :src="item.image_url" mode="aspectFill" />

      <view class="ticket-timeline-card__overlay">
        <text class="ticket-timeline-card__date">{{ monthDayLabel }}</text>

        <view class="ticket-timeline-card__poem">
          <text v-for="line in poemLines" :key="line" class="ticket-timeline-card__poem-line">
            {{ line }}
          </text>
        </view>
      </view>

      <view class="ticket-timeline-card__inner-stroke" />
    </view>

    <image class="ticket-timeline-card__cloud" :src="TICKET_ASSETS.icons.timelineCloud" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.ticket-timeline-card {
  position: relative;
  width: 647rpx;
  max-width: 100%;
  height: 512rpx;
}

.ticket-timeline-card__card {
  position: absolute;
  top: 0;
  width: 564rpx;
  height: 458rpx;
  overflow: hidden;
  border-radius: 42rpx;
  box-shadow: 0 8rpx 8rpx rgba(0, 0, 0, 0.25);
  transition: transform 180ms ease, opacity 180ms ease;
}

.ticket-timeline-card--left .ticket-timeline-card__card {
  left: 0;
}

.ticket-timeline-card--right .ticket-timeline-card__card {
  right: 0;
}

.ticket-timeline-card__image {
  width: 100%;
  height: 100%;
}

.ticket-timeline-card__overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 300rpx;
  background: linear-gradient(180deg, rgba(40, 72, 103, 0) 0%, rgba(37, 71, 101, 0.46) 74.038%, #234664 100%);
}

.ticket-timeline-card__date {
  position: absolute;
  left: 40rpx;
  bottom: 52rpx;
  color: #fff;
  font-family: var(--anima-font-display);
  font-size: 58rpx;
  line-height: 1;
  letter-spacing: 1rpx;
}

.ticket-timeline-card__poem {
  position: absolute;
  right: 28rpx;
  bottom: 26rpx;
  width: 290rpx;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  align-items: center;
}

.ticket-timeline-card__poem-line {
  color: #fff;
  font-family: var(--anima-font-display);
  font-size: 24rpx;
  line-height: 40rpx;
  letter-spacing: 1rpx;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.37);
}

.ticket-timeline-card__inner-stroke {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: inset 0 0 4rpx rgba(255, 255, 255, 0.56);
  pointer-events: none;
}

.ticket-timeline-card__cloud {
  position: absolute;
  top: 214rpx;
  width: 54rpx;
  height: 36rpx;
}

.ticket-timeline-card--left .ticket-timeline-card__cloud {
  right: 0;
}

.ticket-timeline-card--right .ticket-timeline-card__cloud {
  left: 0;
}

.ticket-timeline-card__card--hover {
  opacity: 0.86;
  transform: translateY(-4rpx);
}

@media screen and (max-width: 375px) {
  .ticket-timeline-card {
    width: 100%;
    height: 490rpx;
  }

  .ticket-timeline-card__card {
    width: 540rpx;
    height: 436rpx;
  }

  .ticket-timeline-card__overlay {
    height: 286rpx;
  }

  .ticket-timeline-card__date {
    font-size: 54rpx;
  }

  .ticket-timeline-card__poem {
    width: 276rpx;
  }
}
</style>

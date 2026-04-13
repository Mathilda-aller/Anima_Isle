<script setup lang="ts">
import ticketShareHeaderIcon from "@/modules/ticket/assets/icons/ticket-share-header.svg";
</script>

<template>
  <view class="ticket-share-glyph">
    <image class="ticket-share-glyph__image" :src="ticketShareHeaderIcon" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.ticket-share-glyph {
  width: 28rpx;
  height: 28rpx;
}

.ticket-share-glyph__image {
  width: 100%;
  height: 100%;
}
</style>

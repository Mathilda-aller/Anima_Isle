<script setup lang="ts">
import { TICKET_ASSETS } from "@/modules/ticket/assets";
</script>

<template>
  <view class="ticket-share-glyph">
    <view class="ticket-share-glyph__dot ticket-share-glyph__dot--top">
      <image class="ticket-share-glyph__dot-image" :src="TICKET_ASSETS.icons.shareDot" mode="aspectFit" />
    </view>
    <view class="ticket-share-glyph__dot ticket-share-glyph__dot--left">
      <image class="ticket-share-glyph__dot-image" :src="TICKET_ASSETS.icons.shareDot" mode="aspectFit" />
    </view>
    <view class="ticket-share-glyph__dot ticket-share-glyph__dot--bottom">
      <image class="ticket-share-glyph__dot-image" :src="TICKET_ASSETS.icons.shareDot" mode="aspectFit" />
    </view>

    <image class="ticket-share-glyph__link ticket-share-glyph__link--a" :src="TICKET_ASSETS.icons.shareLinkA" mode="aspectFit" />
    <image class="ticket-share-glyph__link ticket-share-glyph__link--b" :src="TICKET_ASSETS.icons.shareLinkB" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.ticket-share-glyph {
  position: relative;
  width: 28rpx;
  height: 28rpx;
}

.ticket-share-glyph__dot {
  position: absolute;
  width: 10rpx;
  height: 10rpx;
}

.ticket-share-glyph__dot--top {
  right: 1rpx;
  top: 0;
}

.ticket-share-glyph__dot--left {
  left: 0;
  top: 9rpx;
}

.ticket-share-glyph__dot--bottom {
  right: 1rpx;
  bottom: 0;
}

.ticket-share-glyph__dot-image,
.ticket-share-glyph__link {
  width: 100%;
  height: 100%;
}

.ticket-share-glyph__link {
  position: absolute;
}

.ticket-share-glyph__link--a {
  left: 8rpx;
  top: 5rpx;
  width: 10rpx;
  height: 8rpx;
}

.ticket-share-glyph__link--b {
  left: 8rpx;
  top: 15rpx;
  width: 10rpx;
  height: 8rpx;
}
</style>

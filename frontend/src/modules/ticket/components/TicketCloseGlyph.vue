<script setup lang="ts">
import { TICKET_ASSETS } from "@/modules/ticket/assets";
</script>

<template>
  <view class="ticket-close-glyph">
    <image class="ticket-close-glyph__line" :src="TICKET_ASSETS.icons.closeFrontA" mode="aspectFit" />
    <image class="ticket-close-glyph__line" :src="TICKET_ASSETS.icons.closeFrontB" mode="aspectFit" />
  </view>
</template>

<style scoped lang="scss">
.ticket-close-glyph {
  position: relative;
  width: 28rpx;
  height: 28rpx;
}

.ticket-close-glyph__line {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
</style>

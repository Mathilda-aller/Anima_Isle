<script setup lang="ts">
defineProps<{
  label: string;
  icon: string;
}>();
</script>

<template>
  <view class="nav-item">
    <image class="nav-icon" :src="icon" mode="aspectFit" />
    <text class="nav-label">{{ label }}</text>
  </view>
</template>

<style scoped lang="scss">
.nav-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.18em;
}

.nav-icon {
  width: 70%;
  aspect-ratio: 1;
  height: auto;
}

.nav-label {
  font-size: 1em;
  line-height: 1.15;
  color: var(--anima-text-main);
  text-shadow: var(--anima-shadow-title);
  text-align: center;
  font-family: var(--anima-font-display);
  letter-spacing: 0.02em;
  white-space: nowrap;
}
</style>

<script setup lang="ts">
import { onHide, onLaunch, onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { logEvent } from "@/infrastructure/http/tracking";

const authStore = useAuthStore();

onLaunch(async () => {
  authStore.hydrateFromStorage();
  await logEvent("app_launch");
});

onShow(async () => {
  await logEvent("app_show");
});

onHide(async () => {
  await logEvent("app_hide");
});
</script>

<template>
  <view class="app-shell"></view>
</template>

<style lang="scss">
@import "./shared/styles/theme.scss";
</style>

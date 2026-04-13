<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import { SQUARE_ASSETS } from "@/modules/square/assets";
import { ISLAND_CONFIGS, ISLAND_IDS, SCENE_LAYERS, type IslandId } from "@/modules/square/constants/islands";
import { ROUTES } from "@/shared/constants/routes";
import { SHARED_ASSETS } from "@/shared/assets";
import { toLogin } from "@/shared/utils/navigation";
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";

const authStore = useAuthStore();
const selectedIslandId = ref<IslandId | null>(null);

const islands = ISLAND_IDS.map((id) => ISLAND_CONFIGS[id]);
const selectedIsland = computed(() => islands.find((island) => island.id === selectedIslandId.value) ?? null);
const selectedOutlineStyle = computed(() => {
  if (!selectedIsland.value) {
    return {};
  }

  return {
    opacity: selectedIsland.value.outlineOpacity,
    filter: `blur(${selectedIsland.value.outlineBlur})`,
  };
});
const selectedOutlineKeys = computed(() => {
  if (!selectedIslandId.value) {
    return new Set<string>();
  }

  return new Set(ISLAND_CONFIGS[selectedIslandId.value].outlineLayerKeys);
});
const selectionOutlineLayers = computed(() => {
  if (!selectedIslandId.value) {
    return [];
  }

  return sceneLayers.filter((layer) => selectedOutlineKeys.value.has(layer.key));
});
const hotspotIslands = computed(() => islands);
const sceneLayers = SCENE_LAYERS;

onShow(() => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
  }
});

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  uni.switchTab?.({ url: ROUTES.CHAT_HOME });
  uni.reLaunch({ url: ROUTES.CHAT_HOME });
}

function selectIsland(islandId: IslandId) {
  if (selectedIslandId.value === islandId) {
    uni.navigateTo({
      url: `${ROUTES.SQUARE_ISLAND}?island_id=${encodeURIComponent(islandId)}&entry=map`,
    });
    return;
  }

  selectedIslandId.value = islandId;
}
</script>

<template>
  <view class="square-map-page">
    <DarkBackgroundLayer :texture-opacity="0.55" />
    <view class="square-map-page__inner">
      <view class="square-map-page__topbar">
        <view class="square-map-page__back" hover-class="tap-hover" @click="goBack">
          <image class="square-map-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
        </view>
        <text class="square-map-page__title">共感地图</text>
        <view class="square-map-page__topbar-spacer"></view>
      </view>
      <view class="square-map-page__scene">
        <view class="square-map-page__artboard">
          <image
            v-for="layer in sceneLayers"
            :key="layer.key"
            class="square-map-page__layer"
            :src="layer.src"
            :style="layer.style"
            mode="scaleToFill"
          />

          <view class="square-map-page__ribbon-shell">
            <image class="square-map-page__ribbon-glow" :src="SQUARE_ASSETS.icons.ribbonGlow" mode="scaleToFill" />
          </view>

          <image
            v-for="layer in selectionOutlineLayers"
            :key="`outline-${layer.key}`"
            class="square-map-page__layer square-map-page__layer--outline"
            :src="layer.src"
            :style="{ ...layer.style, ...selectedOutlineStyle }"
            mode="scaleToFill"
          />

          <view v-if="selectedIslandId === 'current'" class="square-map-page__ribbon-shell square-map-page__ribbon-shell--outline">
            <image class="square-map-page__ribbon-glow square-map-page__ribbon-glow--outline" :style="selectedOutlineStyle" :src="SQUARE_ASSETS.icons.ribbonGlow" mode="scaleToFill" />
          </view>

          <view
            v-for="island in hotspotIslands"
            :key="island.id"
            class="square-map-page__hotspot"
            :class="{ 'square-map-page__hotspot--active': selectedIslandId === island.id }"
            :style="island.hotspotStyle"
            @click="selectIsland(island.id)"
          ></view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.square-map-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--anima-night-gradient);
}

.square-map-page__inner {
  position: relative;
  min-height: 100vh;
  max-width: 750rpx;
  margin: 0 auto;
  padding: calc(48rpx + env(safe-area-inset-top)) 8rpx env(safe-area-inset-bottom);
}

.square-map-page__topbar {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 44rpx 22rpx 0;
}

.square-map-page__back,
.square-map-page__topbar-spacer {
  width: 46rpx;
  height: 46rpx;
  flex: 0 0 46rpx;
}

.square-map-page__back-icon {
  width: 100%;
  height: 100%;
}

.square-map-page__title {
  color: var(--anima-text-main);
  font-size: 38rpx;
  line-height: 54rpx;
  letter-spacing: 1rpx;
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
}

.square-map-page__scene {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.square-map-page__artboard {
  position: absolute;
  top: 0;
  left: 50%;
  width: 750rpx;
  height: 1624rpx;
  transform: translateX(-50%);
  pointer-events: none;
}

.square-map-page__layer {
  position: absolute;
  display: block;
  pointer-events: none;
  transform-origin: center;
  transition: opacity 180ms ease, filter 180ms ease;
}

.square-map-page__layer--outline,
.square-map-page__ribbon-glow--outline {
  will-change: filter, opacity;
}

.square-map-page__ribbon-shell {
  position: absolute;
  left: 269rpx;
  top: 1128rpx;
  width: 424rpx;
  height: 463rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.square-map-page__ribbon-shell--outline {
  pointer-events: none;
}

.square-map-page__ribbon-shell--outline {
  z-index: 0;
}

.square-map-page__ribbon-glow {
  width: 376rpx;
  height: 278rpx;
  transform: rotate(-61.66deg);
  transition: filter 180ms ease;
}

.square-map-page__hotspot {
  position: absolute;
  z-index: 3;
  background: transparent;
  opacity: 0;
  pointer-events: auto;
}

.square-map-page__hotspot--active {
  opacity: 0;
}
</style>

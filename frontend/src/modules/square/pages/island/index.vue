<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { useAuthStore } from "@/modules/auth/store/auth";
import IslandTagChip from "@/modules/square/components/IslandTagChip.vue";
import { SQUARE_ASSETS } from "@/modules/square/assets";
import {
  DEFAULT_ISLAND_ID,
  ISLAND_CONFIGS,
  SCENE_LAYERS,
  type IslandId,
  type SceneStyle,
} from "@/modules/square/constants/islands";
import { useSquareStore } from "@/modules/square/store/square";
import { useTicketStore } from "@/modules/ticket/store/ticket";
import { ROUTES } from "@/shared/constants/routes";
import { SHARED_ASSETS } from "@/shared/assets";
import DarkBackgroundLayer from "@/shared/components/DarkBackgroundLayer.vue";
import { toLogin } from "@/shared/utils/navigation";

type TagBubbleViewModel = {
  id: string;
  label: string;
  ticketUid: string;
  style: SceneStyle;
  highlighted: boolean;
  fromUserSelection: boolean;
};

const authStore = useAuthStore();
const squareStore = useSquareStore();
const ticketStore = useTicketStore();
const islandId = ref<IslandId>(DEFAULT_ISLAND_ID);
const ticketUid = ref("");
const entry = ref<"map" | "publish">("map");
const sceneReady = ref(false);

const islandConfig = computed(() => ISLAND_CONFIGS[islandId.value]);
const pageTitle = computed(() => `欢迎来到${islandConfig.value.name}`);
const transportMessage = computed(() => {
  if (entry.value !== "publish") {
    return "";
  }

  return `您的心情已被传送至 ${islandConfig.value.englishDisplayName} 岛`;
});
const ticketDetail = computed(() => {
  if (!ticketUid.value) {
    return null;
  }

  return ticketStore.detailMap[ticketUid.value] ?? null;
});
const outlineStyle = computed(() => ({
  opacity: islandConfig.value.outlineOpacity,
  filter: `blur(${islandConfig.value.outlineBlur})`,
}));
const sceneTransform = computed(() => {
  if (!sceneReady.value) {
    return "translate(0, 0) scale(1)";
  }
  return `translate(${islandConfig.value.focusTranslateX}, ${islandConfig.value.focusTranslateY}) scale(${islandConfig.value.focusScale})`;
});
const outlineLayerKeys = computed(() => new Set(islandConfig.value.outlineLayerKeys));
const focusLayerKeys = computed(() => new Set(islandConfig.value.focusLayerKeys));
const selectedOutlineLayers = computed(() =>
  SCENE_LAYERS.filter((layer) => outlineLayerKeys.value.has(layer.key)),
);
const selectedIslandLayers = computed(() =>
  SCENE_LAYERS.filter((layer) => focusLayerKeys.value.has(layer.key)),
);
const islandTagEntries = computed(() => squareStore.islandTagsByIsland[islandConfig.value.backendIslandKey] ?? []);

const islandBubbles = computed<TagBubbleViewModel[]>(() => {
  const slots = islandConfig.value.tagSlots;
  return islandTagEntries.value.slice(0, slots.length).map((tagEntry, index) => ({
    id: `bubble-${index}`,
    label: tagEntry.tag,
    ticketUid: tagEntry.ticket_uid,
    style: {
      left: slots[index].left,
      top: slots[index].top,
      width: slots[index].width,
    },
    highlighted: Boolean(slots[index].highlighted),
    fromUserSelection: tagEntry.from_user_selection,
  }));
});

onLoad(async (query) => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }

  const incomingIslandId = query?.island_id;
  if (typeof incomingIslandId === "string" && incomingIslandId in ISLAND_CONFIGS) {
    islandId.value = incomingIslandId as IslandId;
  }

  if (typeof query?.ticket_uid === "string") {
    ticketUid.value = query.ticket_uid;
  }

  if (query?.entry === "publish") {
    entry.value = "publish";
  }

  if (ticketUid.value) {
    await ticketStore.fetchDetail(ticketUid.value);
  }

  await loadIslandTags();

  setTimeout(() => {
    sceneReady.value = true;
  }, 50);
});

async function loadIslandTags() {
  const preferredTag =
    entry.value === "publish"
      ? (ticketDetail.value?.selected_tags?.[0] ?? squareStore.selectedTags[0])
      : undefined;

  await squareStore.fetchIslandTagEntries(islandConfig.value.backendIslandKey, {
    limit: islandConfig.value.tagSlots.length,
    preferred_tag: preferredTag,
    preferred_ticket_uid: entry.value === "publish" ? ticketUid.value || undefined : undefined,
  });
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  uni.reLaunch({ url: ROUTES.SQUARE_MAP });
}

function openBubble(bubble: TagBubbleViewModel) {
  uni.navigateTo({
    url:
      `${ROUTES.SQUARE_HUG}?ticket_uid=${encodeURIComponent(bubble.ticketUid)}` +
      `&tag=${encodeURIComponent(bubble.label)}` +
      `&island_id=${encodeURIComponent(islandId.value)}`,
  });
}
</script>

<template>
  <view class="square-island-page">
    <DarkBackgroundLayer :texture-opacity="0.55" />
    <view class="square-island-page__topbar">
      <view class="square-island-page__back" hover-class="tap-hover" @click="goBack">
        <image class="square-island-page__back-icon" :src="SHARED_ASSETS.icons.exit" mode="aspectFit" />
      </view>
      <text class="square-island-page__title">共感地图</text>
      <view class="square-island-page__topbar-spacer"></view>
    </view>

    <text v-if="transportMessage" class="square-island-page__transport-message">{{ transportMessage }}</text>
    <text class="square-island-page__hero-title">{{ pageTitle }}</text>
    <text class="square-island-page__hero-subtitle">点击气泡，查看与你共鸣的人……</text>

    <view class="square-island-page__scene" :style="{ height: islandConfig.focusSceneHeight }">
      <view class="square-island-page__viewport">
        <view class="square-island-page__artboard" :style="{ transform: sceneTransform }">
          <image
            v-for="layer in SCENE_LAYERS"
            :key="`bg-${layer.key}`"
            class="square-island-page__layer square-island-page__layer--dimmed"
            :src="layer.src"
            :style="layer.style"
            mode="scaleToFill"
          />

          <view class="square-island-page__ribbon-shell square-island-page__ribbon-shell--dimmed">
            <image class="square-island-page__ribbon-glow" :src="SQUARE_ASSETS.icons.ribbonGlow" mode="scaleToFill" />
          </view>
        </view>

        <view class="square-island-page__artboard square-island-page__artboard--focus" :style="{ transform: sceneTransform }">
          <image
            v-for="layer in selectedOutlineLayers"
            :key="`outline-${layer.key}`"
            class="square-island-page__layer square-island-page__layer--outline"
            :src="layer.src"
            :style="{ ...layer.style, ...outlineStyle }"
            mode="scaleToFill"
          />

          <view v-if="islandId === 'current'" class="square-island-page__ribbon-shell square-island-page__ribbon-shell--outline">
            <image class="square-island-page__ribbon-glow square-island-page__ribbon-glow--outline" :style="outlineStyle" :src="SQUARE_ASSETS.icons.ribbonGlow" mode="scaleToFill" />
          </view>

          <image
            v-for="layer in selectedIslandLayers"
            :key="`focus-${layer.key}`"
            class="square-island-page__layer square-island-page__layer--focus"
            :src="layer.src"
            :style="layer.style"
            mode="scaleToFill"
          />

          <view v-if="islandId === 'current'" class="square-island-page__ribbon-shell square-island-page__ribbon-shell--focus">
            <image class="square-island-page__ribbon-glow" :src="SQUARE_ASSETS.icons.ribbonGlow" mode="scaleToFill" />
          </view>
        </view>

        <view
          v-for="bubble in islandBubbles"
          :key="bubble.id"
          class="square-island-page__bubble"
          :class="{
            'square-island-page__bubble--highlighted': bubble.highlighted,
            'square-island-page__bubble--selected-tag': bubble.fromUserSelection,
          }"
          :style="bubble.style"
          hover-class="square-island-page__bubble--hover"
          @click="openBubble(bubble)"
        >
          <IslandTagChip :label="bubble.label" :avatar-src="SQUARE_ASSETS.images.islandTagAvatar" />
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.square-island-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: var(--anima-night-gradient);
}

.square-island-page__topbar {
  position: relative;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(92rpx + env(safe-area-inset-top)) 32rpx 0;
}

.square-island-page__back,
.square-island-page__topbar-spacer {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
}

.square-island-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
}

.square-island-page__back-icon {
  width: 48rpx;
  height: 48rpx;
}

.square-island-page__title,
.square-island-page__transport-message,
.square-island-page__hero-title,
.square-island-page__hero-subtitle {
  color: var(--anima-text-main);
  text-shadow: var(--anima-shadow-title);
  font-family: var(--anima-font-display);
}

.square-island-page__title {
  font-size: 48rpx;
  line-height: 70rpx;
  letter-spacing: 1rpx;
  text-align: center;
}

.square-island-page__transport-message {
  position: relative;
  z-index: 3;
  display: block;
  margin-top: 36rpx;
  padding: 0 72rpx;
  text-align: center;
  font-size: 30rpx;
  line-height: 44rpx;
  letter-spacing: 1rpx;
}

.square-island-page__hero-title {
  position: relative;
  z-index: 3;
  display: block;
  margin-top: 28rpx;
  text-align: center;
  font-size: 46rpx;
  line-height: 58rpx;
  letter-spacing: 1rpx;
}

.square-island-page__hero-subtitle {
  position: relative;
  z-index: 3;
  display: block;
  margin-top: 20rpx;
  text-align: center;
  font-size: 34rpx;
  line-height: 54rpx;
  letter-spacing: 1rpx;
}

.square-island-page__scene {
  position: relative;
  z-index: 1;
  margin-top: 28rpx;
  overflow: hidden;
}

.square-island-page__viewport {
  position: relative;
  width: 750rpx;
  height: 100%;
  margin: 0 auto;
  overflow: hidden;
}

.square-island-page__artboard {
  position: absolute;
  left: 0;
  top: 0;
  width: 750rpx;
  height: 1624rpx;
  transform-origin: left top;
  transition: transform 520ms cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}

.square-island-page__artboard--focus {
  z-index: 3;
  pointer-events: none;
}

.square-island-page__layer {
  position: absolute;
  display: block;
}

.square-island-page__layer--dimmed {
  filter: brightness(0.34) saturate(0.78);
}

.square-island-page__layer--outline,
.square-island-page__ribbon-glow--outline {
  will-change: filter, opacity;
}

.square-island-page__layer--focus {
  filter: none;
}

.square-island-page__ribbon-shell {
  position: absolute;
  left: 269rpx;
  top: 1128rpx;
  width: 424rpx;
  height: 463rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.square-island-page__ribbon-shell--dimmed {
  filter: brightness(0.34) saturate(0.78);
}

.square-island-page__ribbon-shell--outline,
.square-island-page__ribbon-shell--focus {
  z-index: 0;
}

.square-island-page__ribbon-glow {
  width: 376rpx;
  height: 278rpx;
  transform: rotate(-61.66deg);
}

.square-island-page__dim-mask {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background: rgba(5, 11, 24, 0.72);
  opacity: 1;
}

.square-island-page__bubble {
  position: absolute;
  z-index: 4;
}

.square-island-page__bubble--highlighted :deep(.island-tag-chip),
.square-island-page__bubble--selected-tag :deep(.island-tag-chip) {
  box-shadow: 0 0 8rpx rgba(255, 255, 255, 0.55), 0 0 0 2rpx rgba(255, 255, 255, 0.08);
}

.square-island-page__bubble--selected-tag {
  transform: translateY(-8rpx);
}

.square-island-page__bubble--hover {
  opacity: 0.88;
}
</style>

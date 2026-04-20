<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { AUTH_ASSETS } from "@/modules/auth/assets";
import { useAuthStore } from "@/modules/auth/store/auth";
import { updateUserStyle } from "@/modules/user/api/style";
import { ROUTES } from "@/shared/constants/routes";
import { toLogin } from "@/shared/utils/navigation";
import { setStoredUser, setStyleOnboardingCompleted } from "@/infrastructure/storage/auth";
import { getErrorMessage } from "@/shared/utils/error";

const authStore = useAuthStore();
const selectedStyle = ref<"Warm" | "Dark" | "">("");
const submitting = ref(false);
const errorMsg = ref("");

const canSubmit = computed(() => Boolean(selectedStyle.value) && !submitting.value);

onShow(() => {
  authStore.hydrateFromStorage();
  if (!authStore.isAuthed) {
    toLogin();
    return;
  }
  selectedStyle.value = (authStore.userInfo?.ui_style === "Dark" ? "Dark" : "Warm") as "Warm" | "Dark";
});

function normalizeError(error: unknown): string {
  return getErrorMessage(error, "保存失败，请稍后重试");
}

async function submitSelection() {
  if (!selectedStyle.value || submitting.value) return;

  errorMsg.value = "";
  submitting.value = true;

  try {
    const user = await updateUserStyle(selectedStyle.value);
    authStore.userInfo = {
      id: user.id,
      nickname: user.nickname,
      ui_style: user.ui_style_pref,
    };
    setStoredUser(authStore.userInfo);
    setStyleOnboardingCompleted(true);
    uni.reLaunch({ url: ROUTES.CHAT_HOME });
  } catch (error) {
    errorMsg.value = normalizeError(error);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <view class="style-page">
    <view class="style-page__canvas">
      <view class="heading">
        <text class="title">今天，你想去往哪片海?</text>
        <text class="subtitle">TRUST YOUR THOUGHTS TO THE OCEAN</text>
      </view>

      <view
        class="style-card warm"
        :class="{ active: selectedStyle === 'Warm' }"
        hover-class="card-hover"
        @click="selectedStyle = 'Warm'"
      >
        <image class="card-bg" :src="AUTH_ASSETS.illustrations.styleChooseLight" mode="aspectFill" />
        <view class="card-overlay"></view>
        <view v-if="selectedStyle === 'Warm'" class="card-selected-glow"></view>
        <view class="card-copy left">
          <text class="card-title">澄光暖洋。</text>
          <image class="card-line" :src="AUTH_ASSETS.icons.underline" mode="aspectFit" />
          <text class="card-desc">去捡拾水面上，熠熠生辉的晴朗</text>
        </view>
      </view>

      <view
        class="style-card dark"
        :class="{ active: selectedStyle === 'Dark' }"
        hover-class="card-hover"
        @click="selectedStyle = 'Dark'"
      >
        <image class="card-bg" :src="AUTH_ASSETS.illustrations.styleChooseDark" mode="aspectFill" />
        <view class="card-overlay"></view>
        <view v-if="selectedStyle === 'Dark'" class="card-selected-glow"></view>
        <view class="card-copy right">
          <text class="card-title">星夜静海。</text>
          <image class="card-line" :src="AUTH_ASSETS.icons.underline" mode="aspectFit" />
          <text class="card-desc">去打捞天海间，互为倒影的星与屿</text>
        </view>
      </view>

      <button class="confirm-btn" hover-class="button-hover" :disabled="!canSubmit" @click="submitSelection">
        {{ submitting ? "保存中..." : "我选好了" }}
      </button>

      <text v-if="errorMsg" class="error">{{ errorMsg }}</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.style-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  background: linear-gradient(141.93deg, #b9a698 1.43%, #244665 95.61%);
}

.style-page__canvas {
  width: 100%;
  max-width: 402px;
  min-height: 100vh;
  padding: calc(92px + env(safe-area-inset-top)) 16px calc(44px + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.heading {
  width: 328px;
  max-width: 100%;
  margin: 0 auto;
  text-align: center;
}

.title {
  color: $text-primary;
  font-size: 24px;
  line-height: 1.3;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
}

.subtitle {
  margin-top: 10px;
  display: block;
  color: #eff5ff;
  font-size: 13px;
  letter-spacing: 1.6px;
  line-height: 1.2;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
}

.style-card {
  position: relative;
  margin-top: 18px;
  height: 158px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 18px rgba(255, 255, 255, 0.22);
  border: 1px solid transparent;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.style-card.active {
  border-color: rgba(255, 255, 255, 0.65);
  box-shadow: 0 0 22px rgba(255, 255, 255, 0.3);
}

.style-card.warm {
  width: 92%;
  max-width: 370px;
  border-radius: 18px 60px 60px 18px;
}

.style-card.dark {
  width: 96%;
  max-width: 386px;
  margin-left: auto;
  border-radius: 60px 18px 18px 60px;
}

.card-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.78;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.08);
}

.card-copy {
  position: absolute;
  top: 50px;
  color: $text-primary;
  text-shadow: $anima-shadow-title;
  z-index: 2;
}

.card-copy.left {
  left: 74px;
  text-align: center;
}

.card-copy.right {
  right: 54px;
  text-align: center;
}

.card-title {
  font-size: 20px;
  font-family: $anima-font-display;
}

.card-line {
  margin: 4px auto 0;
  display: block;
  width: 98px;
  height: 4px;
}

.card-desc {
  margin-top: 4px;
  display: block;
  width: 164px;
  font-size: 12px;
  line-height: 1.45;
}

.card-selected-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 100%);
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.12);
  z-index: 1;
}

.confirm-btn {
  margin-top: 40px;
  width: 112px;
  height: 34px;
  line-height: 34px;
  border-radius: 15px;
  border: 1px solid rgba(194, 213, 233, 0.9);
  color: $text-primary;
  font-size: 16px;
  background: transparent;
  text-shadow: $anima-shadow-title;
  font-family: $anima-font-display;
}

.confirm-btn::after {
  border: none;
}

.confirm-btn[disabled] {
  opacity: 0.5;
}

.card-hover {
  opacity: 0.88;
  transform: translateY(-2px);
}

.button-hover {
  opacity: 0.88;
}

.error {
  margin-top: 12px;
  display: block;
  text-align: center;
  color: $anima-text-error;
  font-size: 12px;
}

@media screen and (max-width: 402px) {
  .style-page__canvas {
    padding: calc(120rpx + env(safe-area-inset-top)) 24rpx calc(80rpx + env(safe-area-inset-bottom));
  }

  .heading {
    width: 100%;
  }

  .title {
    font-size: 46rpx;
  }

  .subtitle {
    margin-top: 18rpx;
    font-size: 26rpx;
    letter-spacing: 3rpx;
  }

  .style-card {
    margin-top: 34rpx;
    height: 300rpx;
    box-shadow: 0 0 36rpx rgba(255, 255, 255, 0.4);
    border-width: 1rpx;
  }

  .style-card.active {
    box-shadow: 0 0 44rpx rgba(255, 255, 255, 0.46);
  }

  .style-card.warm {
    max-width: none;
    border-radius: 36rpx 120rpx 120rpx 36rpx;
  }

  .style-card.dark {
    max-width: none;
    border-radius: 120rpx 36rpx 36rpx 120rpx;
  }

  .card-copy {
    top: 96rpx;
  }

  .card-copy.left {
    left: 140rpx;
  }

  .card-copy.right {
    right: 104rpx;
  }

  .card-title {
    font-size: 38rpx;
  }

  .card-line {
    margin-top: 8rpx;
    width: 190rpx;
    height: 8rpx;
  }

  .card-desc {
    margin-top: 8rpx;
    width: 320rpx;
    font-size: 24rpx;
  }

  .card-selected-glow {
    box-shadow: inset 0 0 40rpx rgba(255, 255, 255, 0.12);
  }

  .confirm-btn {
    margin-top: 78rpx;
    width: 220rpx;
    height: 66rpx;
    line-height: 66rpx;
    border-radius: 30rpx;
    border-width: 1rpx;
    font-size: 32rpx;
  }

  .error {
    margin-top: 20rpx;
    font-size: 24rpx;
  }

  .card-hover {
    transform: translateY(-4rpx);
  }
}
</style>

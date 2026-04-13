<script setup lang="ts">
import AuthInputField from "@/modules/auth/components/AuthInputField.vue";
import AuthActionButton from "@/modules/auth/components/AuthActionButton.vue";
import AuthSwitchLink from "@/modules/auth/components/AuthSwitchLink.vue";
import AuthPageShell from "@/modules/auth/components/AuthPageShell.vue";
import AuthRegisterSuccessModal from "@/modules/auth/components/AuthRegisterSuccessModal.vue";
import { AUTH_ASSETS } from "@/modules/auth/assets";
import { useAuthRegisterPage } from "@/modules/auth/composables/useAuthRegisterPage";

const {
  authStore,
  email,
  verificationCode,
  nickname,
  password,
  confirmPassword,
  errorMsg,
  showSuccessModal,
  sendCodeLabel,
  canSendCode,
  sendVerificationCode,
  submitRegistration,
  closeSuccessModal,
  confirmSuccessModal,
  goToLogin,
} = useAuthRegisterPage();
</script>

<template>
  <AuthPageShell title="欢迎注册言屿账号" subtitle="WELCOME" :error-msg="errorMsg">
    <template #form>
      <view class="field-row">
        <AuthInputField v-model="email" type="text" placeholder="邮箱号" />
      </view>

      <view class="field-row field-row--compact">
        <view class="code-row">
          <view class="code-row__input">
            <AuthInputField v-model="verificationCode" type="text" placeholder="验证码" />
          </view>
          <button
            class="code-row__button"
            hover-class="code-row__button--hover"
            :disabled="!canSendCode || authStore.loading"
            @click="sendVerificationCode"
          >
            <text class="code-row__button-text">{{ authStore.loading ? "发送中..." : sendCodeLabel }}</text>
          </button>
        </view>
      </view>

      <view class="field-row field-row--compact">
        <AuthInputField v-model="nickname" type="text" placeholder="昵称" />
      </view>

      <view class="field-row field-row--compact">
        <AuthInputField v-model="password" type="password" placeholder="密码" />
      </view>

      <view class="field-row field-row--compact">
        <AuthInputField v-model="confirmPassword" type="password" placeholder="确认密码" />
      </view>
    </template>

    <template #action>
      <view class="btn-row btn-row--register">
        <AuthActionButton
          :label="authStore.loading ? '注册中...' : 'SIGN UP'"
          :disabled="authStore.loading"
          @click="submitRegistration"
        />
      </view>
    </template>

    <template #switch>
      <view class="switch-row">
        <AuthSwitchLink :label="'已有账号登录'" :underline-src="AUTH_ASSETS.images.switchUnderline" @click="goToLogin" />
      </view>
    </template>

    <template #overlay>
      <AuthRegisterSuccessModal
        v-if="showSuccessModal"
        @close="closeSuccessModal"
        @confirm="confirmSuccessModal"
      />
    </template>
  </AuthPageShell>
</template>

<style scoped lang="scss">
.field-row {
  width: 100%;
  margin-top: 42rpx;
}

.field-row--compact {
  margin-top: 26rpx;
}

.code-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.code-row__input {
  flex: 1;
  min-width: 0;
}

.code-row__button {
  flex-shrink: 0;
  width: 210rpx;
  height: 86rpx;
  border-radius: var(--anima-radius-pill);
  border: none;
  background:
    var(--anima-button-code-sheen),
    var(--anima-surface-field-strong);
  box-shadow: var(--anima-shadow-field-soft);
  border: 1rpx solid var(--anima-line-code-button);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 18rpx;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.code-row__button::after {
  border: none;
}

.code-row__button[disabled] {
  opacity: var(--anima-button-disabled);
}

.code-row__button-text {
  color: var(--anima-text-float);
  font-size: 24rpx;
  letter-spacing: 1rpx;
  line-height: 1.2;
  text-align: center;
  text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.22);
  font-family: var(--anima-font-display);
}

.btn-row {
  margin-top: 190rpx;
}

.btn-row--register {
  margin-top: 120rpx;
}

.switch-row {
  width: 100%;
}

.code-row__button--hover {
  opacity: 0.82;
  transform: scale(0.98);
}

@media screen and (max-width: 420px) {
  .code-row {
    gap: 14rpx;
  }

  .code-row__button {
    width: 196rpx;
  }

  .btn-row--register {
    margin-top: 104rpx;
  }
}
</style>

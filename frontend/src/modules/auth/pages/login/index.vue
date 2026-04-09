<script setup lang="ts">
import AuthInputField from "@/modules/auth/components/AuthInputField.vue";
import AuthActionButton from "@/modules/auth/components/AuthActionButton.vue";
import AuthSwitchLink from "@/modules/auth/components/AuthSwitchLink.vue";
import AuthPageShell from "@/modules/auth/components/AuthPageShell.vue";
import { useAuthLoginPage } from "@/modules/auth/composables/useAuthLoginPage";
import { AUTH_ASSETS } from "@/modules/auth/assets";

const { authStore, email, password, errorMsg, submitLabel, switchLabel, submitAuth, goToRegister } = useAuthLoginPage();
</script>

<template>
  <AuthPageShell title="晚上好，欢迎来到言屿" subtitle="GOOD NIGHT" :error-msg="errorMsg">
    <template #form>
      <view class="field-row">
        <AuthInputField v-model="email" type="text" placeholder="邮箱" />
      </view>
      <view class="field-row">
        <AuthInputField v-model="password" type="password" placeholder="密码" />
      </view>
    </template>

    <template #action>
      <view class="btn-row">
        <AuthActionButton :label="authStore.loading ? '处理中...' : submitLabel" :disabled="authStore.loading" @click="submitAuth" />
      </view>
    </template>

    <template #switch>
      <view class="switch-row">
        <AuthSwitchLink :label="switchLabel" :underline-src="AUTH_ASSETS.images.switchUnderline" @click="goToRegister" />
      </view>
    </template>
  </AuthPageShell>
</template>

<style scoped lang="scss">
.field-row {
  width: 100%;
  margin-top: 42rpx;
}

.btn-row {
  margin-top: 190rpx;
}

.switch-row {
  width: 100%;
}
</style>

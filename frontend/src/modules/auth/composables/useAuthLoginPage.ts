import { computed, ref } from "vue";
import { useAuthStore } from "@/modules/auth/store/auth";
import { ROUTES } from "@/shared/constants/routes";
import { getStyleOnboardingCompleted } from "@/infrastructure/storage/auth";
import { getErrorMessage } from "@/shared/utils/error";

export function useAuthLoginPage() {
  const authStore = useAuthStore();
  authStore.hydrateFromStorage();

  const email = ref("");
  const password = ref("");
  const errorMsg = ref("");

  const submitLabel = computed(() => "LOG IN");
  const switchLabel = computed(() => "新用户注册");

  function normalizeError(error: unknown): string {
    return getErrorMessage(error, "请求失败，请稍后重试");
  }

  async function submitAuth() {
    errorMsg.value = "";
    if (!email.value.trim() || !password.value.trim()) {
      errorMsg.value = "邮箱和密码不能为空";
      return;
    }

    try {
      await authStore.loginEmail(email.value.trim(), password.value.trim());
      uni.reLaunch({ url: getStyleOnboardingCompleted() ? ROUTES.CHAT_HOME : ROUTES.STYLE_PICKER });
    } catch (error) {
      errorMsg.value = normalizeError(error);
    }
  }

  function goToRegister() {
    errorMsg.value = "";
    uni.navigateTo({ url: ROUTES.AUTH_REGISTER });
  }

  return {
    authStore,
    email,
    password,
    errorMsg,
    submitLabel,
    switchLabel,
    submitAuth,
    goToRegister,
  };
}

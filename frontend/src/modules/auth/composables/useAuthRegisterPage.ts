import { computed, onUnmounted, ref } from "vue";
import { useAuthStore } from "@/modules/auth/store/auth";
import { ROUTES } from "@/shared/constants/routes";
import { ApiError } from "@/shared/types/http";
import { setStyleOnboardingCompleted } from "@/infrastructure/storage/auth";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_PATTERN = /^(?=.*[A-Za-z])(?=.*\d).{8,64}$/;
const SEND_CODE_COOLDOWN_SECONDS = 60;

export function useAuthRegisterPage() {
  const authStore = useAuthStore();
  authStore.hydrateFromStorage();

  const email = ref("");
  const verificationCode = ref("");
  const nickname = ref("");
  const password = ref("");
  const confirmPassword = ref("");
  const errorMsg = ref("");
  const showSuccessModal = ref(false);
  const sendCodeCountdown = ref(0);
  let sendCodeTimer: ReturnType<typeof setInterval> | null = null;

  const sendCodeLabel = computed(() => (sendCodeCountdown.value > 0 ? `${sendCodeCountdown.value}s` : "发送验证码"));
  const canSendCode = computed(() => sendCodeCountdown.value === 0 && EMAIL_PATTERN.test(email.value.trim()));

  function normalizeError(error: unknown): string {
    if (error instanceof ApiError) {
      if (typeof error.detail === "string") {
        const errorMap: Record<string, string> = {
          email_exists: "该邮箱已注册，请直接登录",
          verification_code_required: "请先获取邮箱验证码",
          verification_code_invalid: "验证码不正确",
          verification_code_expired: "验证码已过期，请重新获取",
          verification_code_used: "验证码已失效，请重新获取",
          verification_code_send_cooldown: "发送过于频繁，请稍后再试",
          verification_code_daily_limit: "今日发送次数已达上限",
          smtp_not_configured: "邮件服务暂不可用，请稍后再试",
          verification_code_send_failed: "验证码发送失败，请稍后重试",
        };
        return errorMap[error.detail] || error.detail;
      }
      return JSON.stringify(error.detail);
    }
    return "请求失败，请稍后重试";
  }

  function startSendCodeCountdown(seconds: number = SEND_CODE_COOLDOWN_SECONDS) {
    if (sendCodeTimer) clearInterval(sendCodeTimer);
    sendCodeCountdown.value = seconds;
    sendCodeTimer = setInterval(() => {
      if (sendCodeCountdown.value <= 1) {
        sendCodeCountdown.value = 0;
        if (sendCodeTimer) {
          clearInterval(sendCodeTimer);
          sendCodeTimer = null;
        }
        return;
      }
      sendCodeCountdown.value -= 1;
    }, 1000);
  }

  async function sendVerificationCode() {
    errorMsg.value = "";
    if (!EMAIL_PATTERN.test(email.value.trim())) {
      errorMsg.value = "请输入有效邮箱地址";
      return;
    }

    try {
      await authStore.sendEmailVerificationCode(email.value.trim());
      startSendCodeCountdown();
      uni.showToast({ title: "验证码已发送，请检查邮箱", icon: "none" });
    } catch (error) {
      errorMsg.value = normalizeError(error);
    }
  }

  onUnmounted(() => {
    if (sendCodeTimer) {
      clearInterval(sendCodeTimer);
      sendCodeTimer = null;
    }
  });

  function validateForm(): boolean {
    const trimmedEmail = email.value.trim();
    const trimmedNickname = nickname.value.trim();

    if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errorMsg.value = "请输入有效邮箱地址";
      return false;
    }
    if (!/^\d{6}$/.test(verificationCode.value.trim())) {
      errorMsg.value = "请输入 6 位验证码";
      return false;
    }
    if (!trimmedNickname) {
      errorMsg.value = "昵称不能为空";
      return false;
    }
    if (!PASSWORD_PATTERN.test(password.value)) {
      errorMsg.value = "密码需为 8-64 位，且同时包含字母和数字";
      return false;
    }
    if (password.value !== confirmPassword.value) {
      errorMsg.value = "两次输入的密码不一致";
      return false;
    }
    return true;
  }

  async function submitRegistration() {
    errorMsg.value = "";
    if (!validateForm()) return;

    try {
      await authStore.registerEmail(
        email.value.trim(),
        password.value,
        nickname.value.trim(),
        verificationCode.value.trim(),
      );
      showSuccessModal.value = true;
    } catch (error) {
      errorMsg.value = normalizeError(error);
    }
  }

  function closeSuccessModal() {
    showSuccessModal.value = false;
    setStyleOnboardingCompleted(false);
    uni.reLaunch({ url: ROUTES.STYLE_PICKER });
  }

  function confirmSuccessModal() {
    showSuccessModal.value = false;
    setStyleOnboardingCompleted(false);
    uni.reLaunch({ url: ROUTES.STYLE_PICKER });
  }

  function goToLogin() {
    const pages = getCurrentPages();
    if (pages.length > 1) {
      uni.navigateBack();
      return;
    }
    uni.reLaunch({ url: ROUTES.AUTH_LOGIN });
  }

  return {
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
  };
}

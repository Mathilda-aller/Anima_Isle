import { defineStore } from "pinia";
import {
  loginByEmail,
  loginByWechat,
  registerByEmail,
  fetchMe,
  sendRegisterVerificationCode,
} from "@/modules/auth/api/auth";
import { getWechatCode } from "@/infrastructure/platform/wechat";
import {
  clearAuthStorage,
  getStoredToken,
  getStoredUser,
  setStoredToken,
  setStoredUser,
} from "@/infrastructure/storage/auth";
import type { AuthState, AuthTokenResponse, LoginType } from "@/modules/auth/types/auth";
import { logEvent } from "@/infrastructure/http/tracking";

function applyAuthPayload(state: AuthState, payload: AuthTokenResponse, loginType: LoginType): void {
  state.token = payload.access_token;
  state.userInfo = payload.user_info;
  state.loginType = loginType;
  setStoredToken(payload.access_token);
  setStoredUser(payload.user_info);
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: "",
    userInfo: null,
    loginType: "email",
    loading: false,
    initialized: false,
  }),
  getters: {
    isAuthed: (state) => Boolean(state.token),
  },
  actions: {
    hydrateFromStorage() {
      if (this.initialized) return;
      this.token = getStoredToken();
      this.userInfo = getStoredUser();
      this.initialized = true;
    },

    async fetchMeProfile() {
      const me = await fetchMe();
      if (this.userInfo) {
        this.userInfo = {
          ...this.userInfo,
          id: me.id,
          nickname: me.nickname,
          travel_count: me.travel_count,
          ui_style: me.ui_style_pref,
        };
        setStoredUser(this.userInfo);
      }
      return me;
    },

    async loginEmail(email: string, password: string) {
      this.loading = true;
      try {
        const payload = await loginByEmail({
          login_type: "email",
          credential: email,
          password,
        });
        applyAuthPayload(this.$state, payload, "email");
        await this.fetchMeProfile();
        await logEvent("auth_login_success", { login_type: "email" });
      } finally {
        this.loading = false;
      }
    },

    async sendEmailVerificationCode(email: string) {
      this.loading = true;
      try {
        return await sendRegisterVerificationCode({ email });
      } finally {
        this.loading = false;
      }
    },

    async registerEmail(email: string, password: string, nickname?: string, verificationCode?: string) {
      this.loading = true;
      try {
        const payload = await registerByEmail({
          email,
          password,
          nickname,
          verification_code: verificationCode || "",
        });
        applyAuthPayload(this.$state, payload, "email");
        await this.fetchMeProfile();
        await logEvent("auth_register_success", { login_type: "email" });
      } finally {
        this.loading = false;
      }
    },

    async loginWechat() {
      this.loading = true;
      try {
        const code = await getWechatCode();
        const payload = await loginByWechat({ login_type: "wechat", credential: code });
        applyAuthPayload(this.$state, payload, "wechat");
        await this.fetchMeProfile();
        await logEvent("auth_login_success", { login_type: "wechat" });
      } finally {
        this.loading = false;
      }
    },

    logout() {
      clearAuthStorage();
      this.token = "";
      this.userInfo = null;
      this.loginType = "email";
    },
  },
});

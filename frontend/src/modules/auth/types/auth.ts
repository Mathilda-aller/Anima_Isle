export type LoginType = "email" | "wechat";

export interface AuthUserInfo {
  id: number;
  nickname: string;
  ui_style: string;
  travel_count?: number;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user_info: AuthUserInfo;
}

export interface EmailLoginRequest {
  login_type: "email";
  credential: string;
  password: string;
}

export interface WechatLoginRequest {
  login_type: "wechat";
  credential: string;
}

export interface EmailRegisterRequest {
  email: string;
  password: string;
  nickname?: string;
  verification_code: string;
}

export interface EmailVerificationSendRequest {
  email: string;
}

export interface MessageResponse {
  message: string;
}

export interface UserDTO {
  id: number;
  nickname: string;
  avatar_url?: string;
  ui_style_pref: string;
  travel_count: number;
}

export interface AuthState {
  token: string;
  userInfo: AuthUserInfo | null;
  loginType: LoginType;
  loading: boolean;
  initialized: boolean;
}

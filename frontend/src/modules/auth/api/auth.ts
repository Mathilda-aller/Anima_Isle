import { request } from "@/infrastructure/http/request";
import type {
  AuthTokenResponse,
  EmailLoginRequest,
  EmailRegisterRequest,
  EmailVerificationSendRequest,
  MessageResponse,
  UserDTO,
  WechatLoginRequest,
} from "@/modules/auth/types/auth";

export async function loginByEmail(payload: EmailLoginRequest): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse, EmailLoginRequest>({
    path: "/auth/login",
    method: "POST",
    data: payload,
    auth: false,
  });
}

export async function loginByWechat(payload: WechatLoginRequest): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse, WechatLoginRequest>({
    path: "/auth/login",
    method: "POST",
    data: payload,
    auth: false,
  });
}

export async function registerByEmail(payload: EmailRegisterRequest): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse, EmailRegisterRequest>({
    path: "/auth/register",
    method: "POST",
    data: payload,
    auth: false,
  });
}

export async function sendRegisterVerificationCode(payload: EmailVerificationSendRequest): Promise<MessageResponse> {
  return request<MessageResponse, EmailVerificationSendRequest>({
    path: "/auth/register/send-code",
    method: "POST",
    data: payload,
    auth: false,
  });
}

export async function fetchMe(): Promise<UserDTO> {
  return request<UserDTO>({ path: "/users/me", method: "GET" });
}

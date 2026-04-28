import { ApiError } from "@/shared/types/http";

const ERROR_MESSAGE_MAP: Record<string, string> = {
  email_exists: "该邮箱已注册，请直接登录",
  verification_code_required: "请先获取邮箱验证码",
  verification_code_invalid: "验证码不正确",
  verification_code_expired: "验证码已过期，请重新获取",
  verification_code_used: "验证码已失效，请重新获取",
  verification_code_send_cooldown: "发送过于频繁，请稍后再试",
  verification_code_daily_limit: "今日发送次数已达上限",
  smtp_not_configured: "邮件服务暂不可用，请稍后再试",
  verification_code_send_failed: "验证码发送失败，请稍后重试",
  nickname_contains_unsupported_characters: "昵称包含当前环境暂不支持的字符，请调整后再试",
  incorrect_email_or_password: "邮箱或密码错误",
  "Incorrect email or password": "邮箱或密码错误",
  wechat_login_unavailable: "微信登录暂不可用，请稍后再试",
  "Server misconfiguration: Missing WeChat credentials.": "微信登录暂不可用，请稍后再试",
  wechat_server_unreachable: "微信登录服务暂不可用，请稍后再试",
  "Failed to connect to WeChat server": "微信登录服务暂不可用，请稍后再试",
  wechat_code_invalid: "微信登录已失效，请重新尝试",
  unsupported_login_type: "当前登录方式不支持",
  "Unsupported login type": "当前登录方式不支持",
  daily_ticket_limit_reached: "今天的生成次数已达上限，明天再来吧",
  chat_contains_unsupported_characters: "输入内容包含当前环境暂不支持的字符，请调整后再试",
  session_not_found: "当前会话已失效，请重新开始",
  "Session not found": "当前会话已失效，请重新开始",
  "Session no longer accepts input": "当前会话已结束，请重新开始",
  "Stream reply only supports active sessions": "当前会话已结束，请重新开始",
  generation_failed: "生成失败，请稍后重试",
  ticket_persist_failed: "保存结果失败，请稍后重试",
  vector_search_failed: "查找匹配结果失败，请稍后重试",
  audio_transcription_failed: "语音识别失败，请稍后重试",
  ticket_not_found: "未找到这张船票",
  "Ticket not found": "未找到这张船票",
  ticket_not_authorized: "你暂时无权查看这张船票",
  "Not authorized to view this ticket": "你暂时无权查看这张船票",
  "Not authorized": "你暂时无权执行这个操作",
  invalid_style_preference: "所选风格无效，请重新选择",
  "Invalid style preference. Must be 'Warm' or 'Dark'.": "所选风格无效，请重新选择",
  weak_password: "密码太弱，请使用 8-64 位且同时包含字母和数字的密码",
  invalid_or_expired_token: "链接已失效，请重新发起重置密码",
  request_failed: "请求失败，请稍后重试",
  network_error: "网络连接异常，请稍后重试",
  request_aborted: "请求已取消",
  stream_not_supported: "当前环境暂不支持该操作，请稍后重试",
  stream_not_supported_on_h5: "当前浏览器暂不支持该操作，请稍后重试",
};

function parseErrorDetail(detail: string): { code: string; traceId: string } {
  const [code, traceId = ""] = detail.split("|trace_id=");
  return {
    code: code || detail,
    traceId,
  };
}

export function getErrorMessage(error: unknown, fallback = "请求失败，请稍后重试"): string {
  if (!(error instanceof ApiError)) {
    return fallback;
  }

  if (typeof error.detail !== "string") {
    return fallback;
  }

  const { code, traceId } = parseErrorDetail(error.detail);
  const message = ERROR_MESSAGE_MAP[error.detail] || ERROR_MESSAGE_MAP[code] || error.detail;

  if (!traceId || message === error.detail) {
    return message;
  }

  return `${message}（追踪编号 ${traceId}）`;
}

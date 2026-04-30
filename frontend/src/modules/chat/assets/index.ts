import chatVoiceTyping from "./icons/chat-voice-typing.svg";
import chatVoiceRippleInner from "./icons/chat-voice-ripple-inner.svg";
import chatVoiceRippleOuter from "./icons/chat-voice-ripple-outer.svg";
import chatVoiceEndButton from "./icons/chat-voice-end-button.svg";
import chatVoiceReviewButton from "./icons/chat-voice-review-button.svg";
import chatVoicePurpleCircle from "./icons/chat-voice-purple-circle.svg";
import chatVoiceWhiteCircle from "./icons/chat-voice-white-circle.svg";
import chatInputUnderline from "./icons/chat-input-underline.svg";
import inputActionGlow from "./icons/input-action-glow.svg";
import writeEntry from "./icons/imput-write.svg";
import inputVoice from "./icons/input-voice.svg";
import island from "./icons/island.svg";
import ipEllipseGlow from "./icons/ip-ellipse-glow.svg";
import ipStageHalo from "./icons/ip-stage-halo.svg";
import memory from "./icons/memory.svg";
import ticketRerollRefresh from "./icons/ticket-reroll-refresh.svg";
import ticket from "./icons/ticket.svg";
import { SHARED_ASSETS } from "@/shared/assets";

export const CHAT_ASSETS = {
  icons: {
    navMemory: memory,
    navResident: ticket,
    navSquare: island,
    chatInputUnderline,
    ipEllipseGlow,
    ipStageHalo,
    ticketRerollRefresh,
    writeEntry,
    voiceBody: inputVoice,
    voiceHalo: chatVoiceWhiteCircle,
    voicePurpleCircle: chatVoicePurpleCircle,
    voiceEndChat: chatVoiceEndButton,
    voiceReview: chatVoiceReviewButton,
    voiceRippleInner: chatVoiceRippleInner,
    voiceRippleOuter: chatVoiceRippleOuter,
    voiceTyping: chatVoiceTyping,
  },
  images: {
    inputGlow: inputActionGlow,
    islandIpFrame: chatVoiceTyping,
  },
  illustrations: {},
  bg: {
    darkHomeBg: SHARED_ASSETS.bg.darkBg,
  },
} as const;

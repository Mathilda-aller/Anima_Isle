export type ChatGenerationState =
  | "idle"
  | "processing"
  | "reply_streaming"
  | "asset_loading"
  | "finished"
  | "risk_blocked"
  | "error";

export interface ChatStartResponse {
  session_id: string;
  first_question: string;
}

export interface ChatReplyRequest {
  session_id: string;
  content: string;
  is_voice?: boolean;
  duration?: number;
}

export interface ChatVoiceTranscribeResponse {
  session_id: string;
  question_index: number;
  text: string;
  duration: number;
  is_final: boolean;
}

export interface CandidateImage {
  image_id?: string;
  image_url: string;
  poem_content: string;
  image_description?: string;
  emotion_intensity?: string;
  semantic_text?: string;
  distance?: number;
  is_fallback?: boolean;
}

export interface ChatTicketData {
  id: number;
  ticket_uid: string;
  image_url: string;
  poem_content: string;
  island_category: string;
  is_public: boolean;
  created_at: string;
  recommended_tags: string[];
  candidate_images: CandidateImage[];
}

export interface ChatStepResponse {
  session_id: string;
  state: "processing" | "finished" | "risk_blocked";
  reply_text: string;
  ticket_data?: ChatTicketData;
}

export type ChatStreamEventType =
  | "ack"
  | "risk"
  | "empathy_delta"
  | "empathy_done"
  | "asset_started"
  | "asset_ready"
  | "error"
  | "done";

export interface ChatStreamEvent<T = Record<string, unknown>> {
  event: ChatStreamEventType;
  data: T;
}

export interface TicketConfirmRequest {
  ticket_uid: string;
  final_image_url: string;
  final_poem_content: string;
  final_style?: string;
  reroll_count: number;
}

export interface ChatSessionState {
  sessionId: string;
  step: 0 | 1 | 2 | 3;
  q1: string;
  q2: string;
  answer1: string;
  answer2: string;
  pendingFinalAnswer: string;
  pendingFinalAnswerIsVoice: boolean;
  pendingFinalAnswerDuration: number;
  generationState: ChatGenerationState;
  replyText: string;
  ticketDraft: ChatTicketData | null;
  rerollCount: number;
  loading: boolean;
  streamError: string;
}

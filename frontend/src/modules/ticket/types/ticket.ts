export interface TicketDTO {
  id: number;
  ticket_uid: string;
  image_url: string;
  poem_content: string;
  user_diary_summary?: string;
  island_category: string;
  selected_tags: string[];
  selected_image_id?: string;
  is_public: boolean;
  created_at: string;
}

export interface TicketPrintResponse {
  ticket_uid: string;
  is_printed_intent: boolean;
  message: string;
}

export interface TicketTimelineState {
  timeline: TicketDTO[];
  detailMap: Record<string, TicketDTO>;
  skip: number;
  limit: number;
  hasMore: boolean;
  loading: boolean;
}

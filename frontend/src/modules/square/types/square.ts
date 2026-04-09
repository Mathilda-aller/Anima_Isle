export interface MapStarDTO {
  ticket_uid: string;
  image_url: string;
  poem_content: string;
  selected_tags: string[];
  hug_count: number;
  view_count: number;
  created_at: string;
}

export interface CardPublishRequest {
  ticket_uid: string;
  selected_tags: string[];
}

export interface SquareState {
  suggestedTags: string[];
  selectedTags: string[];
  mapStars: MapStarDTO[];
  currentIsland: string;
  loading: boolean;
}

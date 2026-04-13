export interface MapStarDTO {
  ticket_uid: string;
  image_url: string;
  poem_content: string;
  selected_tags: string[];
  hug_count: number;
  view_count: number;
  created_at: string;
}

export interface IslandTagDTO {
  tag: string;
  ticket_uid: string;
  from_user_selection: boolean;
}

export interface CardPublishRequest {
  ticket_uid: string;
  selected_tags: string[];
}

export interface SquareState {
  suggestedTags: string[];
  selectedTags: string[];
  suggestedTagsByTicket: Record<string, string[]>;
  islandTagsByIsland: Record<string, IslandTagDTO[]>;
  mapStars: MapStarDTO[];
  currentIsland: string;
  loading: boolean;
}

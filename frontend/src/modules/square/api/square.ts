import { request } from "@/infrastructure/http/request";
import type { CardPublishRequest, IslandTagDTO, MapStarDTO } from "@/modules/square/types/square";
import type { TicketDTO } from "@/modules/ticket/types/ticket";

export function suggestTags(ticketUid: string) {
  return request<string[]>({
    path: "/square/tags/suggest",
    method: "POST",
    query: { ticket_uid: ticketUid },
    data: {},
  });
}

export function publishTicket(payload: CardPublishRequest) {
  return request<TicketDTO, CardPublishRequest>({
    path: "/square/publish",
    method: "POST",
    data: payload,
  });
}

export function fetchIslandMap(islandKey: string) {
  return request<MapStarDTO[]>({
    path: `/square/map/${islandKey}`,
    method: "GET",
  });
}

export function fetchIslandTags(
  islandKey: string,
  payload: {
    limit: number;
    preferred_tag?: string;
    preferred_ticket_uid?: string;
  },
) {
  return request<IslandTagDTO[]>({
    path: `/square/island-tags/${islandKey}`,
    method: "GET",
    query: payload,
  });
}

export function interactWithCard(ticketUid: string, actionType: "hug" | "view") {
  return request<{ status: string; action: string }>({
    path: `/square/interact/${ticketUid}`,
    method: "POST",
    query: { action_type: actionType },
    data: {},
  });
}

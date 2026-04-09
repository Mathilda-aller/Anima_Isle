import { request } from "@/infrastructure/http/request";
import type { TicketDTO, TicketPrintResponse } from "@/modules/ticket/types/ticket";

export function fetchTicketList(skip = 0, limit = 20) {
  return request<TicketDTO[]>({
    path: "/tickets/list",
    method: "GET",
    query: { skip, limit },
  });
}

export function fetchTicketDetail(ticketUid: string) {
  return request<TicketDTO>({
    path: `/tickets/${ticketUid}`,
    method: "GET",
  });
}

export function recordPrintIntent(ticketUid: string) {
  return request<TicketPrintResponse>({
    path: `/tickets/${ticketUid}/print_intent`,
    method: "POST",
    data: {},
  });
}

import { defineStore } from "pinia";
import { fetchTicketDetail, fetchTicketList, recordPrintIntent } from "@/modules/ticket/api/ticket";
import type { TicketTimelineState } from "@/modules/ticket/types/ticket";
import { logEvent } from "@/infrastructure/http/tracking";

export const useTicketStore = defineStore("ticket", {
  state: (): TicketTimelineState => ({
    timeline: [],
    detailMap: {},
    skip: 0,
    limit: 20,
    hasMore: true,
    loading: false,
  }),
  actions: {
    async refreshList() {
      this.skip = 0;
      this.hasMore = true;
      this.timeline = [];
      await this.fetchList();
    },

    async fetchList() {
      if (!this.hasMore || this.loading) return;
      this.loading = true;
      try {
        const result = await fetchTicketList(this.skip, this.limit);
        this.timeline = [...this.timeline, ...result];
        this.skip += result.length;
        this.hasMore = result.length >= this.limit;
      } finally {
        this.loading = false;
      }
    },

    async fetchDetail(ticketUid: string) {
      const detail = await fetchTicketDetail(ticketUid);
      this.detailMap[ticketUid] = detail;
      return detail;
    },

    async markPrintIntent(ticketUid: string) {
      await recordPrintIntent(ticketUid);
      await logEvent("ticket_print_intent", { ticket_uid: ticketUid });
    },
  },
});

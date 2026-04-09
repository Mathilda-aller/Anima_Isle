import { defineStore } from "pinia";
import { fetchIslandMap, interactWithCard, publishTicket, suggestTags } from "@/modules/square/api/square";
import type { SquareState } from "@/modules/square/types/square";
import { logEvent } from "@/infrastructure/http/tracking";

export const useSquareStore = defineStore("square", {
  state: (): SquareState => ({
    suggestedTags: [],
    selectedTags: [],
    mapStars: [],
    currentIsland: "ISLAND_1",
    loading: false,
  }),
  actions: {
    async suggestTagsForTicket(ticketUid: string) {
      this.loading = true;
      try {
        const tags = await suggestTags(ticketUid);
        this.suggestedTags = tags.length ? tags : ["#心情"];
        this.selectedTags = this.suggestedTags.slice(0, 1);
      } finally {
        this.loading = false;
      }
    },

    toggleTag(tag: string) {
      if (this.selectedTags.includes(tag)) {
        this.selectedTags = this.selectedTags.filter((item) => item !== tag);
        return;
      }
      if (this.selectedTags.length >= 5) return;
      this.selectedTags = [...this.selectedTags, tag];
    },

    async publish(ticketUid: string) {
      const tags = this.selectedTags.length ? this.selectedTags : ["#心情"];
      const result = await publishTicket({
        ticket_uid: ticketUid,
        selected_tags: tags,
      });
      await logEvent("square_publish_success", {
        ticket_uid: ticketUid,
        tags,
      });
      return result;
    },

    async fetchMap(islandKey: string) {
      this.loading = true;
      try {
        this.currentIsland = islandKey;
        this.mapStars = await fetchIslandMap(islandKey);
      } finally {
        this.loading = false;
      }
    },

    async interact(ticketUid: string, actionType: "hug" | "view") {
      await interactWithCard(ticketUid, actionType);
      await logEvent("square_interaction", {
        ticket_uid: ticketUid,
        action_type: actionType,
      });
    },
  },
});

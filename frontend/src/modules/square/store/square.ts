import { defineStore } from "pinia";
import { fetchIslandMap, interactWithCard, publishTicket, suggestTags } from "@/modules/square/api/square";
import type { SquareState } from "@/modules/square/types/square";
import { logEvent } from "@/infrastructure/http/tracking";

function normalizeTags(tags: string[]) {
  const normalized = tags
    .map((tag) => tag.trim())
    .filter(Boolean)
    .map((tag) => (tag.startsWith("#") ? tag : `#${tag}`));

  return normalized.length ? normalized : ["#心情"];
}

export const useSquareStore = defineStore("square", {
  state: (): SquareState => ({
    suggestedTags: [],
    selectedTags: [],
    suggestedTagsByTicket: {},
    mapStars: [],
    currentIsland: "ISLAND_1",
    loading: false,
  }),
  actions: {
    cacheSuggestedTags(ticketUid: string, tags: string[]) {
      const normalized = normalizeTags(tags);
      this.suggestedTagsByTicket = {
        ...this.suggestedTagsByTicket,
        [ticketUid]: normalized,
      };
      this.suggestedTags = normalized;
      this.selectedTags = normalized.slice(0, 1);
      return normalized;
    },

    async suggestTagsForTicket(ticketUid: string, options: { force?: boolean } = {}) {
      const cachedTags = this.suggestedTagsByTicket[ticketUid];
      if (!options.force && cachedTags?.length) {
        this.suggestedTags = cachedTags;
        this.selectedTags = cachedTags.slice(0, 1);
        return cachedTags;
      }

      this.loading = true;
      try {
        const tags = await suggestTags(ticketUid);
        return this.cacheSuggestedTags(ticketUid, tags);
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

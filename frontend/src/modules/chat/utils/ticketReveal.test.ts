import { describe, expect, it } from "vitest";

import {
  canRerollCandidates,
  getFailedTicketRevealImageState,
  getLoadedTicketRevealImageState,
  getNextRerollImageUrl,
  getRerollCandidates,
  getTicketRevealImageState,
} from "@/modules/chat/utils/ticketReveal";

const candidateA = { image_url: "https://img/a.jpg", poem_content: "A" };
const candidateB = { image_url: "https://img/b.jpg", poem_content: "B" };
const candidateC = { image_url: "https://img/c.jpg", poem_content: "C" };

describe("ticketReveal utilities", () => {
  it("derives the expected initial image state", () => {
    expect(getTicketRevealImageState("", "")).toBe("idle");
    expect(getTicketRevealImageState("https://img/a.jpg", "")).toBe("loading");
    expect(getTicketRevealImageState("https://img/a.jpg", "https://img/a.jpg")).toBe("ready");
  });

  it("returns terminal image states for load and error handlers", () => {
    expect(getLoadedTicketRevealImageState()).toBe("ready");
    expect(getFailedTicketRevealImageState()).toBe("error");
  });

  it("filters reroll candidates and disables reroll when fewer than two remain", () => {
    const candidates = [candidateA, { image_url: "", poem_content: "invalid" }, candidateB];

    expect(getRerollCandidates(candidates)).toEqual([candidateA, candidateB]);
    expect(canRerollCandidates([candidateA], false)).toBe(false);
    expect(canRerollCandidates(candidates, false)).toBe(true);
    expect(canRerollCandidates(candidates, true)).toBe(false);
  });

  it("cycles through reroll candidates in order and wraps around", () => {
    const candidates = [candidateA, candidateB, candidateC];

    expect(getNextRerollImageUrl(candidateA.image_url, candidates)).toBe(candidateB.image_url);
    expect(getNextRerollImageUrl(candidateB.image_url, candidates)).toBe(candidateC.image_url);
    expect(getNextRerollImageUrl(candidateC.image_url, candidates)).toBe(candidateA.image_url);
  });

  it("documents duplicate image url behavior for reroll ordering", () => {
    const duplicateCandidates = [candidateA, { image_url: candidateA.image_url, poem_content: "A-2" }, candidateC];

    expect(getNextRerollImageUrl(candidateA.image_url, duplicateCandidates)).toBe(candidateA.image_url);
  });
});

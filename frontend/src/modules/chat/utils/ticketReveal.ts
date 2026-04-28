import type { CandidateImage } from "@/modules/chat/types/chat";

export type TicketRevealImageState = "idle" | "loading" | "ready" | "error";

export function getTicketRevealImageState(imageUrl = "", prefetchedImageUrl = ""): TicketRevealImageState {
  if (!imageUrl) {
    return "idle";
  }
  return imageUrl === prefetchedImageUrl ? "ready" : "loading";
}

export function getLoadedTicketRevealImageState(): TicketRevealImageState {
  return "ready";
}

export function getFailedTicketRevealImageState(): TicketRevealImageState {
  return "error";
}

export function getRerollCandidates(candidateImages: CandidateImage[] = []): CandidateImage[] {
  return candidateImages.filter((item) => !!item.image_url);
}

export function canRerollCandidates(candidateImages: CandidateImage[] = [], confirmLoading = false): boolean {
  return getRerollCandidates(candidateImages).length > 1 && !confirmLoading;
}

export function getNextRerollImageUrl(currentImageUrl: string, candidateImages: CandidateImage[] = []): string | null {
  const rerollCandidates = getRerollCandidates(candidateImages);
  if (!rerollCandidates.length) {
    return null;
  }

  const currentIndex = rerollCandidates.findIndex((item) => item.image_url === currentImageUrl);
  const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % rerollCandidates.length : 0;
  return rerollCandidates[nextIndex]?.image_url ?? null;
}

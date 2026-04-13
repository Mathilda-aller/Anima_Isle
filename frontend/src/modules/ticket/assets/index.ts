import ticketCollectIcon from "./icon-ticket-collect.svg";
import ticketPublishIcon from "./icon-ticket-publish.svg";
import ticketCloseFrontA from "./icons/ticket-close-front-a.svg";
import ticketCloseFrontB from "./icons/ticket-close-front-b.svg";
import ticketDiaryDivider from "./icons/ticket-diary-divider.svg";
import ticketDiaryDotInner from "./icons/ticket-diary-dot-inner.svg";
import ticketDiaryDotOuter from "./icons/ticket-diary-dot-outer.svg";
import ticketShareDot from "./icons/ticket-share-dot.svg";
import ticketShareLinkA from "./icons/ticket-share-link-a.svg";
import ticketShareLinkB from "./icons/ticket-share-link-b.svg";
import ticketShareIcon from "./icons/ticket-share.svg";
import ticketTimelineCurveLeft from "./icons/ticket-timeline-curve-left.svg";
import ticketTimelineCurveRight from "./icons/ticket-timeline-curve-right.svg";
import ticketTimelineCloud from "./icons/ticket-timeline-cloud.svg";
import ticketTimelinePathVector24 from "./paths/ticket-timeline-path-vector24.svg";
import ticketTimelinePathVector25 from "./paths/ticket-timeline-path-vector25.svg";

export const TICKET_ASSETS = {
  icons: {
    collect: ticketCollectIcon,
    closeFrontA: ticketCloseFrontA,
    closeFrontB: ticketCloseFrontB,
    diaryDivider: ticketDiaryDivider,
    diaryDotInner: ticketDiaryDotInner,
    diaryDotOuter: ticketDiaryDotOuter,
    publish: ticketPublishIcon,
    shareDot: ticketShareDot,
    shareLinkA: ticketShareLinkA,
    shareLinkB: ticketShareLinkB,
    share: ticketShareIcon,
    timelineCurveLeft: ticketTimelineCurveLeft,
    timelineCurveRight: ticketTimelineCurveRight,
    timelineCloud: ticketTimelineCloud,
  },
  paths: {
    vector24: ticketTimelinePathVector24,
    vector25: ticketTimelinePathVector25,
  },
  images: {},
  illustrations: {},
  bg: {},
} as const;

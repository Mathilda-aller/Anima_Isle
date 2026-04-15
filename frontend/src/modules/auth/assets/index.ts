import underline from "./icons/underline.svg";
import registerSuccessCheckmark from "./register-success/checkmark.svg";
import registerSuccessClose from "./register-success/close.svg";
import residentCurveLeft from "./resident/resident-curve-left.svg";
import residentCurveRight from "./resident/resident-curve-right.svg";
import residentPassShell from "./resident/resident-pass-shell.svg";
import communityCloseA from "./community/community-close-a.svg";
import communityCloseB from "./community/community-close-b.svg";
import residentTicketDividerHorizontal from "./resident-ticket/resident-ticket-divider-horizontal.svg";
import residentTicketDividerVertical from "./resident-ticket/resident-ticket-divider-vertical.svg";
import residentTicketShell from "./resident-ticket/resident-ticket-shell.svg";
import { SHARED_ASSETS } from "@/shared/assets";

const styleChooseDark = "/static/auth/style-choose-dark.png";
const styleChooseLight = "/static/auth/style-choose-light.png";
const residentScene = "/static/auth/resident-scene.png";

export const AUTH_ASSETS = {
  icons: {
    underline,
    registerSuccessCheckmark,
    registerSuccessClose,
  },
  images: {
    switchUnderline: underline,
  },
  illustrations: {
    islandIpLogo: SHARED_ASSETS.icons.ipNight,
    styleChooseDark,
    styleChooseLight,
    residentScene,
  },
  bg: {
    darkGlobalBg: SHARED_ASSETS.bg.darkBg,
  },
  resident: {
    communityCloseA,
    communityCloseB,
    curveLeft: residentCurveLeft,
    curveRight: residentCurveRight,
    passShell: residentPassShell,
  },
  residentTicket: {
    dividerHorizontal: residentTicketDividerHorizontal,
    dividerVertical: residentTicketDividerVertical,
    shell: residentTicketShell,
  },
} as const;

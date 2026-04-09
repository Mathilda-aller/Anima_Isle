import darkBg from "./bg/dark-bg.png";
import exitIcon from "./icons/exit.svg";
import ipDark from "./icons/ip-dark.svg";
import ipEyeEllipse from "./icons/ip-eye-ellipse.svg";
import ipFaceVector from "./icons/ip-face-vector.svg";
import ipNightHeadBack from "./icons/ip-night-head-back.svg";
import ipNightHeadFront from "./icons/ip-night-head-front.svg";

export const SHARED_ASSETS = {
  bg: {
    darkBg,
  },
  icons: {
    exit: exitIcon,
    ipDark,
    ipNight: ipDark,
    ipEyeEllipse,
    ipFaceVector,
    ipNightHeadBack,
    ipNightHeadFront,
  },
} as const;

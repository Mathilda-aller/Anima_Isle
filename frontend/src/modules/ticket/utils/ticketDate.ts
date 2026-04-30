const CHINA_TIME_ZONE = "Asia/Shanghai";
const CHINA_OFFSET = "+08:00";
const DATE_ONLY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const TIME_ZONE_PATTERN = /(?:Z|[+-]\d{2}:?\d{2})$/i;
const CHINESE_DIGITS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];

function normalizeDateInput(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (TIME_ZONE_PATTERN.test(trimmed)) return trimmed;
  if (DATE_ONLY_PATTERN.test(trimmed)) return `${trimmed}T00:00:00${CHINA_OFFSET}`;

  const normalized = trimmed.includes("T") ? trimmed : trimmed.replace(" ", "T");
  return `${normalized}${CHINA_OFFSET}`;
}

export function parseTicketDate(value?: string | null): Date | null {
  if (!value) return null;

  const date = new Date(normalizeDateInput(value));
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

function getChinaDateParts(value?: string | null) {
  const date = parseTicketDate(value);
  if (!date) return null;

  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: CHINA_TIME_ZONE,
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);

  const partValue = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? "";
  const year = Number(partValue("year"));
  const month = Number(partValue("month"));
  const day = Number(partValue("day"));
  const hour = partValue("hour");
  const minute = partValue("minute");

  if (!year || !month || !day || !hour || !minute) return null;
  return { date, year, month, day, hour, minute };
}

function getSeason(month: number): string {
  if (month >= 3 && month <= 5) return "春";
  if (month >= 6 && month <= 8) return "夏";
  if (month >= 9 && month <= 11) return "秋";
  return "冬";
}

export function formatTicketSeasonLabel(value?: string | null, fallback = ""): string {
  const parts = getChinaDateParts(value);
  if (!parts) return fallback;

  const yearText = String(parts.year)
    .split("")
    .map((digit) => CHINESE_DIGITS[Number(digit)] ?? digit)
    .join("");

  return `${yearText}年·${getSeason(parts.month)}`;
}

export function formatTicketMonthDay(value?: string | null, fallback = "May 23"): string {
  const parts = getChinaDateParts(value);
  if (!parts) return fallback;

  return new Intl.DateTimeFormat("en-US", {
    timeZone: CHINA_TIME_ZONE,
    month: "short",
    day: "numeric",
  }).format(parts.date);
}

export function formatTicketWeekday(value?: string | null, fallback = "THURSDAY"): string {
  const parts = getChinaDateParts(value);
  if (!parts) return fallback;

  return new Intl.DateTimeFormat("en-US", {
    timeZone: CHINA_TIME_ZONE,
    weekday: "long",
  })
    .format(parts.date)
    .toUpperCase();
}

export function formatTicketMetaTime(value?: string | null, fallback = "言屿记录"): string {
  const parts = getChinaDateParts(value);
  if (!parts) return fallback;

  return `${parts.hour}:${parts.minute} 言屿`;
}

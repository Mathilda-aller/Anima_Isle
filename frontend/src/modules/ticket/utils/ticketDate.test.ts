import { describe, expect, it } from "vitest";

import {
  formatTicketMetaTime,
  formatTicketMonthDay,
  formatTicketSeasonLabel,
  formatTicketWeekday,
  parseTicketDate,
} from "@/modules/ticket/utils/ticketDate";

describe("ticketDate utilities", () => {
  it("treats timezone-less timestamps as China time", () => {
    const createdAt = "2026-04-25T10:48:00";

    expect(formatTicketSeasonLabel(createdAt)).toBe("二零二六年·春");
    expect(formatTicketMonthDay(createdAt)).toBe("Apr 25");
    expect(formatTicketWeekday(createdAt)).toBe("SATURDAY");
    expect(formatTicketMetaTime(createdAt)).toBe("10:48 言屿");
  });

  it("formats offset-aware UTC timestamps in China time", () => {
    const createdAt = "2026-04-25T02:48:00Z";

    expect(formatTicketMonthDay(createdAt)).toBe("Apr 25");
    expect(formatTicketWeekday(createdAt)).toBe("SATURDAY");
    expect(formatTicketMetaTime(createdAt)).toBe("10:48 言屿");
  });

  it("treats date-only values as China local midnight", () => {
    expect(formatTicketMonthDay("2026-04-25")).toBe("Apr 25");
    expect(formatTicketWeekday("2026-04-25")).toBe("SATURDAY");
    expect(formatTicketMetaTime("2026-04-25")).toBe("00:00 言屿");
  });

  it("returns fallbacks for invalid or missing timestamps", () => {
    expect(parseTicketDate("not-a-date")).toBeNull();
    expect(formatTicketSeasonLabel("not-a-date")).toBe("");
    expect(formatTicketMonthDay(null)).toBe("May 23");
    expect(formatTicketWeekday(undefined)).toBe("THURSDAY");
    expect(formatTicketMetaTime("")).toBe("言屿记录");
  });

  it("uses China-time calendar boundaries", () => {
    const utcBoundary = "2026-04-30T16:30:00Z";
    const chinaLocal = "2026-04-30T23:30:00";

    expect(formatTicketMonthDay(utcBoundary)).toBe("May 1");
    expect(formatTicketWeekday(utcBoundary)).toBe("FRIDAY");
    expect(formatTicketMetaTime(utcBoundary)).toBe("00:30 言屿");
    expect(formatTicketMonthDay(chinaLocal)).toBe("Apr 30");
    expect(formatTicketMetaTime(chinaLocal)).toBe("23:30 言屿");
  });
});

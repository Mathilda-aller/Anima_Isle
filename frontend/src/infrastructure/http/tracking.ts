import { request } from "@/infrastructure/http/request";

interface EventPayload {
  event_name: string;
  user_id?: number;
  properties?: Record<string, unknown>;
}

export async function logEvent(eventName: string, properties: Record<string, unknown> = {}): Promise<void> {
  const payload: EventPayload = {
    event_name: eventName,
    properties,
  };

  try {
    await request({
      path: "/log/event",
      method: "POST",
      data: payload,
      auth: false,
    });
  } catch {
    // tracking failures must never block UX
  }
}

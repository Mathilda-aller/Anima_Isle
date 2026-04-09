export interface ApiErrorShape {
  statusCode: number;
  detail: string | Record<string, unknown>;
  requestId?: string;
}

export class ApiError extends Error implements ApiErrorShape {
  statusCode: number;
  detail: string | Record<string, unknown>;
  requestId?: string;

  constructor(payload: ApiErrorShape) {
    super(typeof payload.detail === "string" ? payload.detail : "Request failed");
    this.name = "ApiError";
    this.statusCode = payload.statusCode;
    this.detail = payload.detail;
    this.requestId = payload.requestId;
  }
}

export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "DELETE"
  | "OPTIONS"
  | "HEAD"
  | "TRACE"
  | "CONNECT";

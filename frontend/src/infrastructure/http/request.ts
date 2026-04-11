import { clearAuthStorage, getStoredToken } from "@/infrastructure/storage/auth";
import { toLogin } from "@/shared/utils/navigation";
import { ApiError, type HttpMethod } from "@/shared/types/http";

interface RequestOptions<TData = unknown> {
  path: string;
  method?: HttpMethod;
  data?: TData;
  query?: Record<string, string | number | boolean | undefined | null>;
  auth?: boolean;
  headers?: Record<string, string>;
  timeout?: number;
}

interface RequestResult<T> {
  data: T;
  statusCode: number;
  header: Record<string, string>;
}

interface AbortableRequestTask {
  abort?: () => void;
}

interface BaseResponseEnvelope<T = unknown> {
  code: number;
  message: string;
  data?: T;
}

export interface CancelableRequest<T> {
  promise: Promise<T>;
  cancel: () => void;
}

const EXTERNAL_API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();

function getApiBase(): string {
  // #ifdef H5
  return "/api";
  // #endif

  return EXTERNAL_API_BASE || "/api";
}

export function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base = `${getApiBase()}${normalizedPath}`;
  if (!query) return base;

  const pairs: string[] = [];
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  });

  if (!pairs.length) return base;
  return `${base}?${pairs.join("&")}`;
}

function normalizeError(statusCode: number, payload: unknown, requestId?: string): ApiError {
  let detail: string | Record<string, unknown> = "request_failed";
  if (typeof payload === "string" && payload.trim()) {
    detail = payload;
  } else if (typeof payload === "object" && payload !== null && "detail" in payload) {
    detail = (payload as { detail: string | Record<string, unknown> }).detail;
  }

  return new ApiError({
    statusCode,
    detail,
    requestId,
  });
}

function buildAbortError(): ApiError {
  return new ApiError({
    statusCode: 0,
    detail: "request_aborted",
  });
}

export function isRequestAbortedError(error: unknown): boolean {
  return error instanceof ApiError && error.detail === "request_aborted";
}

function isBaseResponseEnvelope(payload: unknown): payload is BaseResponseEnvelope {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "code" in payload &&
    "message" in payload &&
    typeof (payload as { code?: unknown }).code === "number" &&
    typeof (payload as { message?: unknown }).message === "string"
  );
}

function shouldUseH5FetchForFormData(data: unknown): data is FormData {
  return (
    typeof window !== "undefined" &&
    typeof document !== "undefined" &&
    typeof fetch === "function" &&
    typeof FormData !== "undefined" &&
    data instanceof FormData
  );
}

async function resolveFetchPayload<TResponse>(response: Response): Promise<RequestResult<TResponse>> {
  const contentType = response.headers.get("content-type") || "";
  let data: TResponse;

  if (contentType.includes("application/json")) {
    data = (await response.json()) as TResponse;
  } else {
    data = (await response.text()) as TResponse;
  }

  const header: Record<string, string> = {};
  response.headers.forEach((value, key) => {
    header[key] = value;
  });

  return {
    data,
    statusCode: response.status,
    header,
  };
}

function resolveRequestResponse<TResponse>(response: RequestResult<TResponse>): TResponse {
  if (response.statusCode >= 200 && response.statusCode < 300) {
    if (isBaseResponseEnvelope(response.data)) {
      return response.data.data as TResponse;
    }
    return response.data;
  }

  const requestId = response.header["x-request-id"] || response.header["X-Request-Id"];
  const apiError = normalizeError(response.statusCode, response.data, requestId);

  if (apiError.statusCode === 401) {
    clearAuthStorage();
    toLogin();
  }

  throw apiError;
}

export function requestCancelable<TResponse, TData = unknown>(
  options: RequestOptions<TData>,
): CancelableRequest<TResponse> {
  const token = getStoredToken();
  const isFormData = typeof FormData !== "undefined" && options.data instanceof FormData;
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };

  if (options.auth !== false && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const url = buildUrl(options.path, options.query);
  let cancelled = false;
  let requestTask: AbortableRequestTask | null = null;

  if (shouldUseH5FetchForFormData(options.data)) {
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const promise = fetch(url, {
      method: options.method || "GET",
      body: options.data,
      headers,
      signal: controller?.signal,
    })
      .then((response) => resolveFetchPayload<TResponse>(response))
      .then((response) => resolveRequestResponse(response))
      .catch((error: unknown) => {
        if ((error as Error | undefined)?.name === "AbortError") {
          throw buildAbortError();
        }
        throw error;
      });

    return {
      promise,
      cancel: () => {
        cancelled = true;
        if (cancelled) {
          controller?.abort();
        }
      },
    };
  }

  const promise = new Promise<RequestResult<TResponse>>((resolve, reject) => {
    requestTask = uni.request({
      url,
      method: options.method || "GET",
      data: options.data as any,
      timeout: options.timeout ?? 15000,
      header: headers,
      success: (res) => {
        resolve({
          data: res.data as TResponse,
          statusCode: res.statusCode,
          header: (res.header || {}) as Record<string, string>,
        });
      },
      fail: (err) => {
        reject(
          cancelled
            ? buildAbortError()
            : new ApiError({
                statusCode: 0,
                detail: err.errMsg || "network_error",
              }),
        );
      },
    }) as unknown as AbortableRequestTask;
  });

  return {
    promise: promise.then((response) => resolveRequestResponse(response)),
    cancel: () => {
      cancelled = true;
      requestTask?.abort?.();
    },
  };
}

export async function request<TResponse, TData = unknown>(
  options: RequestOptions<TData>,
): Promise<TResponse> {
  return requestCancelable<TResponse, TData>(options).promise;
}

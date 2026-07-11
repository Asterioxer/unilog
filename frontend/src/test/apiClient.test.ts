import { describe, it, expect } from "vitest";
import { apiClient } from "../services/apiClient";

interface MockInterceptorResponse {
  fulfilled: (value: unknown) => unknown;
  rejected: (error: unknown) => Promise<unknown>;
}

describe("apiClient axios instance", () => {
  it("should configure base URL and default headers", () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
    expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
  });

  it("handles interceptor success callback", () => {
    const responseInterceptors = apiClient.interceptors.response as unknown as {
      handlers: Array<{ fulfilled: (v: unknown) => unknown }>;
    };
    const handler = responseInterceptors.handlers[0];
    const mockResponse = { status: 200, data: { success: true } };
    const result = handler.fulfilled(mockResponse);
    expect(result).toEqual(mockResponse);
  });

  it("maps response error schemas to customized error formats", async () => {
    const responseInterceptors = apiClient.interceptors.response as unknown as {
      handlers: Array<MockInterceptorResponse>;
    };
    const handler = responseInterceptors.handlers[0];
    const mockError = {
      response: {
        data: {
          success: false,
          error: {
            code: "INVALID_LOG",
            message: "Validation failed parsing file input",
            details: {}
          }
        }
      }
    };

    try {
      await handler.rejected(mockError);
      expect(true).toBe(false); // Should not reach here
    } catch (err: unknown) {
      const apiError = err as { code: string; message: string };
      expect(apiError.code).toBe("INVALID_LOG");
      expect(apiError.message).toBe("Validation failed parsing file input");
    }
  });

  it("maps generic errors using fallback schemas", async () => {
    const responseInterceptors = apiClient.interceptors.response as unknown as {
      handlers: Array<MockInterceptorResponse>;
    };
    const handler = responseInterceptors.handlers[0];
    const mockError = {
      code: "ECONNREFUSED",
      message: "Connection refused",
      response: undefined
    };

    try {
      await handler.rejected(mockError);
      expect(true).toBe(false); // Should not reach here
    } catch (err: unknown) {
      const apiError = err as { code: string; message: string };
      expect(apiError.code).toBe("ECONNREFUSED");
      expect(apiError.message).toBe("Connection refused");
    }
  });
});

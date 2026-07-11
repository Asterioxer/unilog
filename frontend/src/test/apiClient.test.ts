import { describe, it, expect } from "vitest";
import { apiClient } from "../services/apiClient";

describe("apiClient axios instance", () => {
  it("should configure base URL and default headers", () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
    expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
  });

  it("handles interceptor success callback", () => {
    const handlers = (apiClient.interceptors.response as any).handlers[0];
    const mockResponse = { status: 200, data: { success: true } };
    const result = handlers.fulfilled(mockResponse);
    expect(result).toEqual(mockResponse);
  });

  it("maps response error schemas to customized error formats", async () => {
    const handlers = (apiClient.interceptors.response as any).handlers[0];
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
      await handlers.rejected(mockError);
      expect(true).toBe(false); // Should not reach here
    } catch (err: any) {
      expect(err.code).toBe("INVALID_LOG");
      expect(err.message).toBe("Validation failed parsing file input");
    }
  });

  it("maps generic errors using fallback schemas", async () => {
    const handlers = (apiClient.interceptors.response as any).handlers[0];
    const mockError = {
      code: "ECONNREFUSED",
      message: "Connection refused",
      response: undefined
    };

    try {
      await handlers.rejected(mockError);
      expect(true).toBe(false); // Should not reach here
    } catch (err: any) {
      expect(err.code).toBe("ECONNREFUSED");
      expect(err.message).toBe("Connection refused");
    }
  });
});

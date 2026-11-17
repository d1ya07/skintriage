import { AxiosError, type AxiosResponse } from "axios";
import { describe, expect, it } from "vitest";
import { getErrorMessage } from "./errors";

function axiosErr(status?: number, data?: unknown) {
  const response = status
    ? ({ status, data, statusText: "", headers: {}, config: {} } as unknown as AxiosResponse)
    : undefined;
  return new AxiosError("Request failed", "ERR", undefined, undefined, response);
}

describe("getErrorMessage", () => {
  it("uses FastAPI's string detail", () => {
    expect(getErrorMessage(axiosErr(401, { detail: "Invalid email or password" }))).toBe(
      "Invalid email or password",
    );
  });

  it("uses the first validation error and strips the prefix", () => {
    const err = axiosErr(422, { detail: [{ msg: "Value error, Password is too long" }] });
    expect(getErrorMessage(err)).toBe("Password is too long");
  });

  it("explains network errors", () => {
    expect(getErrorMessage(axiosErr())).toMatch(/can't reach the server/i);
  });

  it("falls back for unknown errors", () => {
    expect(getErrorMessage(new Error("boom"), "Oops")).toBe("Oops");
  });
});

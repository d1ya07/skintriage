import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Disclaimer } from "./Disclaimer";
import { StatusBadge } from "./StatusBadge";

describe("UI components", () => {
  it("disclaimer says it's not a diagnostic device", () => {
    render(<Disclaimer />);
    expect(screen.getByText(/not a diagnostic device/i)).toBeInTheDocument();
  });

  it("status badge shows a readable label", () => {
    render(<StatusBadge status="cancelled" />);
    expect(screen.getByText("Cancelled")).toBeInTheDocument();
  });
});

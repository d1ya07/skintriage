import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import type { TriageResult } from "@/types";
import { TriageResultCard } from "./TriageResultCard";

const result: TriageResult = {
  id: 3,
  image_url: "/api/uploads/images/1/abc.jpg",
  predicted_condition: "mel",
  predicted_label: "Melanoma",
  confidence: 0.8,
  urgency_level: "high",
  specialist_type: "Dermato-oncologist",
  urgent_referral: true,
  advice: "See a specialist.",
  reasons: ["Top suggestion: Melanoma (80%)"],
  probabilities: [{ code: "mel", label: "Melanoma", probability: 0.8 }],
  model_version: null,
  created_at: "2026-11-17T10:00:00Z",
  disclaimer: "Not a diagnosis.",
};

describe("TriageResultCard for doctors", () => {
  it("hides the patient booking button when showBookButton is false", () => {
    render(
      <MemoryRouter>
        <TriageResultCard result={result} showImage={false} showBookButton={false} />
      </MemoryRouter>,
    );
    expect(screen.queryByRole("link", { name: /book/i })).not.toBeInTheDocument();
    expect(screen.getByText("Melanoma", { selector: "h2" })).toBeInTheDocument();
  });
});

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import type { TriageResult } from "@/types";
import { TriageResultCard } from "./TriageResultCard";
import { UrgencyBadge } from "./UrgencyBadge";

const base: TriageResult = {
  id: 7,
  image_url: "/api/uploads/images/1/abc.jpg",
  predicted_condition: "nv",
  predicted_label: "Melanocytic nevus (mole)",
  confidence: 0.62,
  urgency_level: "high",
  specialist_type: "Dermato-oncologist",
  urgent_referral: true,
  advice: "Some advice.",
  reasons: ["Melanoma probability is 30%, at or above the 25% safety threshold"],
  probabilities: [
    { code: "nv", label: "Melanocytic nevus (mole)", probability: 0.62 },
    { code: "mel", label: "Melanoma", probability: 0.3 },
  ],
  model_version: "efficientnet_b0@2026-11-17",
  created_at: "2026-11-17T10:00:00Z",
  disclaimer: "This is an AI-assisted triage suggestion, not a diagnosis.",
};

function renderCard(result: TriageResult) {
  render(
    <MemoryRouter>
      <TriageResultCard result={result} showImage={false} />
    </MemoryRouter>,
  );
}

describe("TriageResultCard", () => {
  it("shows the urgent banner and an urgent booking link for high urgency", () => {
    renderCard(base);
    expect(screen.getByText(/urgent referral recommended/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /book urgent appointment/i })).toHaveAttribute(
      "href",
      "/doctors?specialty=Dermato-oncologist&triage=7",
    );
    expect(screen.getByText(/safety threshold/i)).toBeInTheDocument();
  });

  it("has no urgent banner for low urgency", () => {
    renderCard({ ...base, urgency_level: "low", urgent_referral: false, specialist_type: "General Physician" });
    expect(screen.queryByText(/urgent referral recommended/i)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /book matched specialist/i })).toHaveAttribute(
      "href",
      "/doctors?specialty=General%20Physician&triage=7",
    );
  });

  it("urgency badge is human readable", () => {
    render(<UrgencyBadge level="moderate" />);
    expect(screen.getByText("Moderate urgency")).toBeInTheDocument();
  });
});

describe("Uncertain results", () => {
  it("shows 'Uncertain result' instead of a confident condition name", () => {
    renderCard({ ...base, uncertain: true, confidence: 0.41, urgency_level: "moderate", urgent_referral: false });
    expect(screen.getByRole("heading", { name: "Uncertain result" })).toBeInTheDocument();
    expect(screen.getByText(/outside what the model can assess/i)).toBeInTheDocument();
  });
});

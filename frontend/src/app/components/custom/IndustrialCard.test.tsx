import { render, screen } from "@testing-library/react";
import { IndustrialCard } from "./IndustrialCard";

describe("IndustrialCard", () => {
  it("renders title, subtitle, and children", () => {
    render(
      <IndustrialCard title="Primary Surface" subtitle="Command briefing">
        <div>card-body</div>
      </IndustrialCard>
    );

    expect(screen.getByText("Primary Surface")).toBeInTheDocument();
    expect(screen.getByText("Command briefing")).toBeInTheDocument();
    expect(screen.getByText("card-body")).toBeInTheDocument();
  });

  it("exposes the tone variant as a stable attribute", () => {
    const { container } = render(
      <IndustrialCard title="Rail Surface" tone="rail">
        <div>rail-body</div>
      </IndustrialCard>
    );

    expect(container.firstChild).toHaveAttribute("data-tone", "rail");
  });

  it("renders a custom header slot when provided", () => {
    render(
      <IndustrialCard title="Secondary Surface" headerSlot={<button type="button">Inspect</button>}>
        <div>body</div>
      </IndustrialCard>
    );

    expect(screen.getByRole("button", { name: "Inspect" })).toBeInTheDocument();
  });
});

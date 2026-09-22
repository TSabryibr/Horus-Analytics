import { render, screen } from "@testing-library/react";
import { Brain } from "lucide-react";
import { CommandHeader } from "./CommandHeader";

describe("CommandHeader", () => {
  it("renders the command header hierarchy and status items", () => {
    render(
      <CommandHeader
        eyebrow="Oracle Command"
        title="AI Price Forecast"
        description="Market breadth and volatility squeeze analysis."
        icon={<Brain className="h-7 w-7" />}
        statusItems={[
          { label: "Mode", value: "Live", tone: "primary" },
          { label: "Sync", value: "Fresh", tone: "success" },
        ]}
        actions={<button type="button">Refresh</button>}
      />
    );

    expect(screen.getByText("Oracle Command")).toBeInTheDocument();
    expect(screen.getByText("AI Price Forecast")).toBeInTheDocument();
    expect(screen.getByText("Market breadth and volatility squeeze analysis.")).toBeInTheDocument();
    expect(screen.getByText("Mode")).toBeInTheDocument();
    expect(screen.getByText("Live")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh" })).toBeInTheDocument();
  });
});

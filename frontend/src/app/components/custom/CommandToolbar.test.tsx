import { render, screen } from "@testing-library/react";
import { CommandToolbar } from "./CommandToolbar";

describe("CommandToolbar", () => {
  it("renders the toolbar label, children, and trailing actions", () => {
    render(
      <CommandToolbar
        label="Ticker Command"
        description="Shared controls should wrap without changing chrome."
        trailing={<button type="button">Analyze</button>}
      >
        <input aria-label="Ticker" />
        <button type="button">Hotkey</button>
      </CommandToolbar>
    );

    expect(screen.getByText("Ticker Command")).toBeInTheDocument();
    expect(screen.getByText("Shared controls should wrap without changing chrome.")).toBeInTheDocument();
    expect(screen.getByLabelText("Ticker")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
  });
});

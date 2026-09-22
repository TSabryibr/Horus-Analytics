import { fireEvent, render, screen, within } from "@testing-library/react";
import { IndustrialNavbar } from "./IndustrialNavbar";
import { ROUTES, TOP_NAV_GROUPS } from "../config/navigation";

jest.mock("../hooks/useSidebarRuntime", () => ({
  useSidebarRuntime: jest.fn(),
}));

jest.mock("next/image", () => {
  function MockNextImage({ alt, priority: _priority, ...props }: { alt: string; priority?: boolean }) {
    return <img alt={alt} {...props} />;
  }

  return MockNextImage;
});

import { useSidebarRuntime } from "../hooks/useSidebarRuntime";

const routeTranslations: Record<string, string> = {
  "nav.dashboard": "Terminal Dashboard",
  "nav.telegram": "Telegram Rail",
  "nav.scanner": "Market Scanner",
  "nav.analytics": "Market Analytics",
  "nav.analysis_report": "Analysis Report",
  "nav.live": "Live Monitor",
  "nav.strategy": "Strategy Core",
  "nav.optimization": "Strategy Lab",
  "nav.news": "Alpha News",
  "nav.audit_trail": "Performance Audit",
  "nav.oracle": "AI Oracle",
  "nav.whales": "Whale Tracker",
  "nav.traps": "Trap Detector",
  "nav.arbitrage": "Arbitrage Hub",
  "nav.seasonality": "Seasonality",
  "nav.sectors": "Sector Analysis",
  "nav.simulation": "Simulation Room",
  "nav.portfolio": "Portfolio",
  "nav.subscribers": "Subscribers",
  "nav.executionQuality": "Execution Quality",
  "nav.settings": "Settings",
};

describe("IndustrialNavbar", () => {
  beforeEach(() => {
    (useSidebarRuntime as jest.Mock).mockReturnValue({
      pathname: "/oracle",
      t: (key: string) => routeTranslations[key] ?? key,
      toggleLanguage: jest.fn(),
      language: "en",
      systemStatus: {
        code: "FRESH",
        label: "Synced",
        dotClass: "bg-emerald-500",
        textClass: "text-emerald-400",
      },
      portfolios: [
        { id: 8, name: "Daily Simulation", type: "SYSTEM" },
        { id: 11, name: "Stress Matrix", type: "SYSTEM" },
        { id: 21, name: "EGX Breakout Pine", type: "STRATEGY" },
        { id: 3, name: "Operator Book", type: "USER" },
      ],
      activePortfolioId: 11,
      defaultPortfolioId: 8,
      setActivePortfolioId: jest.fn(),
      setDefaultSystemPortfolioId: jest.fn(),
      lastSyncDisplay: "14:29",
      backendSourceLabel: "DirectFN Feed",
    });
  });

  it("renders the shared command ribbon chrome", () => {
    render(<IndustrialNavbar />);

    expect(screen.getByAltText("Horus Logo")).toBeInTheDocument();
    expect(screen.getByText("Horus Analytics")).toBeInTheDocument();
    expect(screen.getByText("EGX Command")).toBeInTheDocument();
    expect(screen.getByText("DirectFN Feed")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open system status" })).toHaveAttribute("href", "/status");
    expect(screen.getAllByLabelText("Toggle language")).toHaveLength(1);
    expect(screen.getByTestId("command-ribbon-grid")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Intelligence navigation group" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Oversight navigation group" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "System navigation group" })).toBeInTheDocument();
  });

  it("hosts the portfolio command cluster in the live navbar", () => {
    render(<IndustrialNavbar />);

    expect(screen.getByText("Active Portfolio")).toBeInTheDocument();
    expect(screen.getByText("Stress Matrix")).toBeInTheDocument();
    expect(screen.getByText("Daily Simulation")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open portfolio command deck" }));

    expect(screen.getByText("SYSTEM PORTFOLIOS")).toBeInTheDocument();
    expect(screen.getByText("STRATEGY PORTFOLIOS")).toBeInTheDocument();
    expect(screen.getByText("USER PORTFOLIOS")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Activate Daily Simulation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Activate EGX Breakout Pine" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Set Daily Simulation as default" })).toBeDisabled();
    expect(screen.getAllByText("Cannot Default").length).toBeGreaterThanOrEqual(1);
  });

  it("activates any portfolio and only allows SYSTEM rows to become the default", () => {
    const setActivePortfolioId = jest.fn();
    const setDefaultSystemPortfolioId = jest.fn();

    (useSidebarRuntime as jest.Mock).mockReturnValue({
      pathname: "/oracle",
      t: (key: string) => key,
      toggleLanguage: jest.fn(),
      language: "en",
      systemStatus: {
        code: "FRESH",
        label: "Synced",
        dotClass: "bg-emerald-500",
        textClass: "text-emerald-400",
      },
      portfolios: [
        { id: 8, name: "Daily Simulation", type: "SYSTEM" },
        { id: 11, name: "Stress Matrix", type: "SYSTEM" },
        { id: 21, name: "EGX Breakout Pine", type: "STRATEGY" },
        { id: 3, name: "Operator Book", type: "USER" },
      ],
      activePortfolioId: 11,
      defaultPortfolioId: 8,
      setActivePortfolioId,
      setDefaultSystemPortfolioId,
      lastSyncDisplay: "14:29",
      backendSourceLabel: "DirectFN Feed",
    });

    render(<IndustrialNavbar />);

    fireEvent.click(screen.getByRole("button", { name: "Open portfolio command deck" }));
    fireEvent.click(screen.getByRole("button", { name: "Activate Operator Book" }));
    fireEvent.click(screen.getByRole("button", { name: "Set Stress Matrix as default" }));

    expect(setActivePortfolioId).toHaveBeenCalledWith(3);
    expect(setDefaultSystemPortfolioId).toHaveBeenCalledWith(11);
    expect(screen.queryByRole("button", { name: "Set Operator Book as default" })).not.toBeInTheDocument();
  });

  it("marks the active route and keeps the route strip navigable without horizontal scrolling", () => {
    render(<IndustrialNavbar />);

    const intelligenceGroup = screen.getByRole("button", { name: "Intelligence navigation group" });
    const dashboardLink = screen.getByLabelText("Terminal Dashboard (HOME)");
    const telegramLink = screen.getByLabelText("Telegram Rail (RAIL)");
    const ribbonGrid = screen.getByTestId("command-ribbon-grid");

    expect(intelligenceGroup).toHaveAttribute("aria-expanded", "false");
    expect(dashboardLink).toHaveAttribute("href", "/");
    expect(telegramLink).toHaveAttribute("href", "/telegram");
    expect(ribbonGrid.className).not.toContain("overflow-x-auto");
  });

  it("opens grouped route chambers and dismisses them with escape", () => {
    render(<IndustrialNavbar />);

    const intelligenceGroup = screen.getByRole("button", { name: "Intelligence navigation group" });
    fireEvent.click(intelligenceGroup);

    expect(intelligenceGroup).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu", { name: "Intelligence routes" })).toBeInTheDocument();
    expect(screen.getByLabelText("AI Oracle (ORCL)")).toHaveAttribute("href", "/oracle");

    fireEvent.keyDown(document, { key: "Escape" });

    expect(intelligenceGroup).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("menu", { name: "Intelligence routes" })).not.toBeInTheDocument();
  });

  it("keeps a grouped route chamber open when focus arrives before the click", () => {
    render(<IndustrialNavbar />);

    const systemGroup = screen.getByRole("button", { name: "System navigation group" });
    fireEvent.focus(systemGroup);
    fireEvent.click(systemGroup);

    expect(systemGroup).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu", { name: "System routes" })).toBeInTheDocument();
    expect(screen.getByLabelText("Settings (CFG)")).toHaveAttribute("href", "/settings");
  });

  it("opens every domain chamber from navigation data with matching route labels and links", () => {
    render(<IndustrialNavbar />);

    const routeByHref = new Map(ROUTES.map((route) => [route.href, route]));

    TOP_NAV_GROUPS.forEach((group) => {
      const button = screen.getByRole("button", { name: `${group.label} navigation group` });

      fireEvent.click(button);

      const menu = screen.getByRole("menu", { name: `${group.label} routes` });
      const menuItems = within(menu).getAllByRole("menuitem");
      expect(menuItems).toHaveLength(group.routes.length);

      group.routes.forEach((href) => {
        const route = routeByHref.get(href);
        expect(route).toBeDefined();
        const translatedLabel = routeTranslations[route!.label];
        expect(translatedLabel).toBeDefined();
        expect(within(menu).getByLabelText(`${translatedLabel} (${route!.shortLabel})`)).toHaveAttribute("href", href);
      });
    });
  });
});

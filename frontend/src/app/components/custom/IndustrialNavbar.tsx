import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ChevronDown, Clock, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { ROUTES, TOP_NAV_ANCHORS, TOP_NAV_GROUPS } from "../config/navigation";
import { useSidebarRuntime } from "../hooks/useSidebarRuntime";

type PortfolioRecord = {
  id: number;
  name: string;
  type: string;
};

function PortfolioCommandCluster({
  portfolios,
  activePortfolioId,
  defaultPortfolioId,
  setActivePortfolioId,
  setDefaultSystemPortfolioId,
  deletePortfolio,
}: {
  portfolios: PortfolioRecord[];
  activePortfolioId: number;
  defaultPortfolioId: number;
  setActivePortfolioId: (portfolioId: number) => void;
  setDefaultSystemPortfolioId: (portfolioId: number) => Promise<boolean>;
  deletePortfolio: (portfolioId: number) => Promise<boolean>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const normalizedFilter = filter.trim().toLowerCase();
  const visiblePortfolios = normalizedFilter
    ? portfolios.filter((portfolio) => `${portfolio.name} ${portfolio.type}`.toLowerCase().includes(normalizedFilter))
    : portfolios;
  const systemPortfolios = visiblePortfolios.filter((portfolio) => portfolio.type === "SYSTEM");
  const strategyPortfolios = visiblePortfolios.filter((portfolio) => portfolio.type === "STRATEGY");
  const userPortfolios = visiblePortfolios.filter((portfolio) => portfolio.type === "USER");
  const activePortfolio = portfolios.find((portfolio) => portfolio.id === activePortfolioId) ?? null;
  const defaultPortfolio = portfolios.find((portfolio) => portfolio.id === defaultPortfolioId) ?? null;

  return (
    <div ref={containerRef} className="relative block w-full min-w-[12rem] flex-1 2xl:max-w-[18rem]">
      <button
        type="button"
        aria-expanded={isOpen}
        aria-label="Open portfolio command deck"
        onClick={() => setIsOpen((current) => !current)}
        className={cn(
          "section-surface-muted industrial-corner flex min-h-[4rem] w-full items-center gap-3 rounded-[1rem] px-3 py-2 text-left transition",
          isOpen ? "border-primary/35 bg-white/[0.07] shadow-[0_0_20px_rgba(6,182,212,0.15)]" : "hover:border-primary/25 hover:bg-white/[0.05]"
        )}
      >
        <div className="flex size-10 shrink-0 items-center justify-center rounded-[0.9rem] border border-cyan-400/20 bg-cyan-400/10 text-cyan-100 shadow-[0_0_0_1px_rgba(34,211,238,0.08)]">
          <span className="font-mono text-[10px] font-black uppercase tracking-[0.24em]">PF</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="meta-label text-slate-500">Active Portfolio</span>
            {activePortfolio ? (
              <span className="command-chip command-chip-primary rounded-[999px] px-2.5 py-0.5 text-[9px]">
                Active
              </span>
            ) : null}
          </div>
          <div className="mt-1 flex min-w-0 items-center gap-2">
            <span className="truncate text-[12px] font-black uppercase tracking-[0.18em] text-white">
              {activePortfolio?.name || "Unassigned"}
            </span>
            {activePortfolio?.type ? (
              <span className={cn(
                "rounded px-1.5 py-0.5 text-[8.5px] font-mono font-bold uppercase tracking-[0.15em]",
                activePortfolio.type === "SYSTEM" ? "bg-purple-500/20 text-purple-300 border border-purple-500/30" :
                activePortfolio.type === "STRATEGY" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" :
                "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
              )}>
                {activePortfolio.type}
              </span>
            ) : null}
          </div>
          <div className="mt-1 flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-400">
            <span className="text-slate-500">Default</span>
            <span className="truncate text-cyan-100">{defaultPortfolio?.name || "Choose System Default"}</span>
          </div>
        </div>
      </button>

      {isOpen ? (
        <div 
          className="section-surface industrial-corner absolute right-0 top-full mt-3 z-[130] w-[min(38rem,calc(100vw-1.5rem))] rounded-[1.4rem] p-5 shadow-[0_24px_80px_rgba(2,6,23,0.7)] border border-cyan-500/20"
          style={{ position: "absolute" }}
        >
          <div className="flex items-start justify-between gap-4 border-b border-white/8 pb-4">
            <div className="min-w-0">
              <div className="meta-label text-cyan-400 font-bold">Portfolio Control</div>
              <div className="mt-1 text-lg font-black uppercase tracking-[0.18em] text-white">Portfolio Switcher</div>
              <p className="mt-1 max-w-md text-xs leading-5 text-slate-400">
                Choose the active book across all trading screens. SYSTEM portfolios can also become the startup default.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close portfolio command deck"
              className="rounded-[0.9rem] border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-black uppercase tracking-[0.24em] text-slate-300 transition hover:border-white/16 hover:text-white"
            >
              Close
            </button>
          </div>

          <div className="mt-4 rounded-[1.1rem] border border-cyan-500/20 bg-[linear-gradient(135deg,rgba(8,145,178,0.15),rgba(15,23,42,0.8))] px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[9px] font-black uppercase tracking-[0.28em] text-cyan-300/80">Global Default</div>
                <div className="mt-1 truncate text-sm font-semibold text-cyan-50 flex items-center gap-2">
                  <span className="size-2 rounded-full bg-cyan-400 animate-pulse" />
                  {defaultPortfolio?.name || "UNASSIGNED"}
                </div>
              </div>
              <div className="text-right">
                <div className="text-[9px] font-black uppercase tracking-[0.26em] text-slate-400">Active</div>
                <div className="mt-1 truncate text-sm font-semibold text-white flex items-center gap-2 justify-end">
                  <span className="size-2 rounded-full bg-emerald-400" />
                  {activePortfolio?.name || "NONE"}
                </div>
              </div>
            </div>
          </div>

          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Filter portfolios"
            className="mt-4 w-full rounded-[1rem] border border-white/10 bg-slate-950/85 px-3.5 py-2.5 text-sm font-medium text-slate-200 outline-none placeholder:text-slate-500 focus:border-cyan-500/40"
          />

          <div className="mt-4 grid gap-4 lg:grid-cols-3 max-h-[22rem] overflow-y-auto pr-1">
            <PortfolioCommandSection
              title="SYSTEM PORTFOLIOS"
              emptyMessage="No system portfolios match the current filter."
              portfolios={systemPortfolios}
              activePortfolioId={activePortfolioId}
              defaultPortfolioId={defaultPortfolioId}
              setActivePortfolioId={setActivePortfolioId}
              setDefaultSystemPortfolioId={setDefaultSystemPortfolioId}
              deletePortfolio={deletePortfolio}
            />
            <PortfolioCommandSection
              title="STRATEGY PORTFOLIOS"
              emptyMessage="No strategy portfolios match the current filter."
              portfolios={strategyPortfolios}
              activePortfolioId={activePortfolioId}
              defaultPortfolioId={defaultPortfolioId}
              setActivePortfolioId={setActivePortfolioId}
              setDefaultSystemPortfolioId={setDefaultSystemPortfolioId}
              deletePortfolio={deletePortfolio}
              onClose={() => setIsOpen(false)}
            />
            <PortfolioCommandSection
              title="USER PORTFOLIOS"
              emptyMessage="No user portfolios match the current filter."
              portfolios={userPortfolios}
              activePortfolioId={activePortfolioId}
              defaultPortfolioId={defaultPortfolioId}
              setActivePortfolioId={setActivePortfolioId}
              setDefaultSystemPortfolioId={setDefaultSystemPortfolioId}
              deletePortfolio={deletePortfolio}
              onClose={() => setIsOpen(false)}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PortfolioCommandSection({
  title,
  emptyMessage,
  portfolios,
  activePortfolioId,
  defaultPortfolioId,
  setActivePortfolioId,
  setDefaultSystemPortfolioId,
  deletePortfolio,
  onClose,
}: {
  title: string;
  emptyMessage: string;
  portfolios: PortfolioRecord[];
  activePortfolioId: number;
  defaultPortfolioId: number;
  setActivePortfolioId: (portfolioId: number) => void;
  setDefaultSystemPortfolioId: (portfolioId: number) => Promise<boolean>;
  deletePortfolio: (portfolioId: number) => Promise<boolean>;
  onClose?: () => void;
}) {
  return (
    <section className="min-w-0">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">{title}</h2>
        <span className="text-[9px] font-mono uppercase tracking-[0.24em] text-slate-600">{portfolios.length}</span>
      </div>

      <div className="space-y-2.5">
        {portfolios.length === 0 ? (
          <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-3 text-xs text-slate-400">
            {emptyMessage}
          </div>
        ) : null}

        {portfolios.map((portfolio) => {
          const isActive = portfolio.id === activePortfolioId;
          const isDefault = portfolio.id === defaultPortfolioId;
          const isSystem = portfolio.type === "SYSTEM";

          return (
            <div 
              key={portfolio.id} 
              className={cn(
                "rounded-[1rem] border px-3 py-3 transition-all",
                isActive 
                  ? "border-cyan-400/40 bg-cyan-950/20 shadow-[0_0_15px_rgba(6,182,212,0.12)]" 
                  : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className={cn("truncate text-sm font-semibold", isActive ? "text-cyan-100 font-bold" : "text-slate-100")}>
                    {portfolio.name}
                  </div>
                  <div className="mt-1 text-[10px] uppercase tracking-[0.22em] text-slate-500">{portfolio.type}</div>
                </div>
                <div className="flex flex-wrap justify-end gap-1">
                  {isActive ? (
                    <span className="command-chip command-chip-primary rounded-[999px] px-2.5 py-1 text-[9px]">Active</span>
                  ) : null}
                  {isDefault ? (
                    <span className="command-chip command-chip-warning rounded-[999px] px-2.5 py-1 text-[9px]">Default</span>
                  ) : null}
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setActivePortfolioId(portfolio.id)}
                  aria-label={`Activate ${portfolio.name}`}
                  className={cn(
                    "rounded-[0.85rem] border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] transition",
                    isActive
                      ? "border-cyan-400/35 bg-cyan-500/10 text-cyan-100"
                      : "border-white/10 bg-slate-950/75 text-slate-300 hover:border-cyan-500/30 hover:text-cyan-100"
                  )}
                >
                  Activate
                </button>
                {isSystem ? (
                  <button
                    type="button"
                    onClick={() => {
                      void setDefaultSystemPortfolioId(portfolio.id);
                    }}
                    aria-label={`Set ${portfolio.name} as default`}
                    disabled={isDefault}
                    className={cn(
                      "rounded-[0.85rem] border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] transition disabled:cursor-default",
                      isDefault
                        ? "border-amber-400/30 bg-amber-500/10 text-amber-100"
                        : "border-sky-500/30 bg-sky-500/10 text-sky-100 hover:border-sky-400/50"
                    )}
                  >
                    {isDefault ? "Default" : "Set Default"}
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={async () => {
                        if (confirm(`Are you sure you want to delete portfolio "${portfolio.name}"?`)) {
                          await deletePortfolio(portfolio.id);
                        }
                      }}
                      aria-label={`Delete ${portfolio.name}`}
                      className="rounded-[0.85rem] border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-red-100 hover:border-red-400/50 hover:bg-red-500/20 transition"
                    >
                      Delete
                    </button>
                    <span className="rounded-[0.85rem] border border-orange-500/30 bg-orange-500/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-orange-100">
                      Cannot Default
                    </span>
                  </>
                )}
              </div>
            </div>
          );
        })}

        {title === "USER PORTFOLIOS" ? (
          <Link
            href="/portfolio?section=management"
            onClick={onClose}
            className="mt-3 flex items-center justify-center gap-2 rounded-[0.9rem] border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-xs font-bold uppercase tracking-wider text-cyan-300 transition hover:bg-cyan-500/20 hover:border-cyan-400/50"
          >
            <Upload size={13} className="text-cyan-400" /> + Import Subscriber Book
          </Link>
        ) : null}
      </div>
    </section>
  );
}

export const IndustrialNavbar = () => {
  const {
    pathname,
    t,
    toggleLanguage,
    language,
    systemStatus,
    lastSyncDisplay,
    backendSourceLabel,
    portfolios,
    activePortfolioId,
    defaultPortfolioId,
    setActivePortfolioId,
    setDefaultSystemPortfolioId,
    deletePortfolio,
    startSimulation,
  } = useSidebarRuntime();

  const isRouteActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);

  const routeByHref = new Map(ROUTES.map((route) => [route.href, route]));
  const navRef = useRef<HTMLElement | null>(null);
  const [openGroupId, setOpenGroupId] = useState<string | null>(null);
  const anchorRoutes = TOP_NAV_ANCHORS
    .map((href) => routeByHref.get(href))
    .filter((route): route is (typeof ROUTES)[number] => Boolean(route));
  const groupedRoutes = TOP_NAV_GROUPS.map((group) => ({
    ...group,
    routes: group.routes
      .map((href) => routeByHref.get(href))
      .filter((route): route is (typeof ROUTES)[number] => Boolean(route)),
  }));

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!navRef.current) {
        return;
      }

      if (!navRef.current.contains(event.target as Node)) {
        setOpenGroupId(null);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpenGroupId(null);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <nav ref={navRef} className="industrial-border sticky top-0 z-[110] overflow-visible border-x-0 border-t-0 bg-slate-950/90 backdrop-blur-xl">
      <div className="mx-auto grid min-h-[var(--chrome-nav-height)] w-full max-w-[1700px] grid-cols-[minmax(0,1fr)] gap-3 px-3 py-3 sm:px-4 xl:grid-cols-[auto_minmax(0,1fr)] xl:items-start xl:px-5 2xl:grid-cols-[auto_minmax(0,1fr)_auto] 2xl:items-center 2xl:px-6">
        <Link
          href="/"
          className="group section-surface-muted industrial-corner order-1 col-span-1 flex min-w-0 items-center gap-3 rounded-[1.15rem] px-3 py-2.5 transition hover:border-primary/25 hover:bg-white/[0.05] xl:min-h-[4rem]"
        >
          <div className="relative flex size-11 shrink-0 items-center justify-center rounded-[1rem] bg-[linear-gradient(135deg,rgba(34,211,238,0.18),rgba(8,145,178,0.28))] shadow-[0_12px_32px_rgba(34,211,238,0.18)] ring-1 ring-cyan-300/20">
            <Image
              src="/android-chrome-192x192.png"
              alt="Horus Logo"
              width={44}
              height={45}
              className="h-auto w-full object-contain transition duration-300 group-hover:scale-[1.04]"
              style={{ height: 'auto' }}
              priority
            />
          </div>
          <div className="min-w-0">
            <span className="block truncate font-heading text-[1.15rem] font-black uppercase tracking-[0.24em] text-white">
              Horus Analytics
            </span>
            <span className="block truncate font-mono text-[8px] uppercase tracking-[0.34em] text-amber-200/70">
              EGX Command
            </span>
          </div>
        </Link>

        <div className="order-2 col-span-1 flex min-w-0 flex-col items-stretch gap-2 sm:flex-row sm:items-stretch sm:justify-end xl:col-span-1 xl:justify-self-end 2xl:order-3 2xl:gap-3">
          <PortfolioCommandCluster
            portfolios={portfolios}
            activePortfolioId={activePortfolioId}
            defaultPortfolioId={defaultPortfolioId}
            setActivePortfolioId={setActivePortfolioId}
            setDefaultSystemPortfolioId={setDefaultSystemPortfolioId}
            deletePortfolio={deletePortfolio}
          />

          <Link
            href="/status"
            aria-label="Open system status"
            title="Open system status"
            className="section-surface-muted industrial-corner flex min-w-0 flex-1 items-center gap-3 rounded-[1rem] px-3 py-2 transition hover:border-primary/25 hover:bg-white/[0.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 2xl:max-w-[12rem] min-h-[4rem]"
          >
            <div className={cn("mt-0.5 size-2 shrink-0 rounded-full shadow-[0_0_14px_currentColor]", systemStatus.dotClass)} />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="meta-label text-slate-500">System</span>
                <span className={cn("truncate text-[10px] font-black uppercase tracking-[0.24em]", systemStatus.textClass)}>
                  {systemStatus.label}
                </span>
              </div>
              <div className="mt-0.5 flex items-center gap-2 text-[10px] font-mono text-slate-400">
                <span className="truncate">{backendSourceLabel}</span>
                <span className="text-slate-700">/</span>
                <span className="tabular-nums">{lastSyncDisplay}</span>
              </div>
            </div>
          </Link>

          <button
            type="button"
            onClick={() => void startSimulation()}
            title="Matrix Travel"
            aria-label="Matrix Travel"
            className="section-surface-muted industrial-corner group flex h-auto min-h-[3.25rem] w-[3.25rem] shrink-0 items-center justify-center rounded-[1rem] text-slate-400 transition hover:border-amber-400/30 hover:bg-amber-400/10 hover:text-amber-300 xl:min-h-[4rem] xl:w-[4rem]"
          >
            <Clock className="size-4 transition-transform duration-500 group-hover:-rotate-45" />
          </button>

          <button
            type="button"
            onClick={toggleLanguage}
            aria-label="Toggle language"
            className="section-surface-muted industrial-corner flex h-auto min-h-[3.25rem] w-[3.25rem] shrink-0 items-center justify-center rounded-[1rem] text-[10px] font-black uppercase tracking-[0.24em] text-slate-200 transition hover:border-primary/30 hover:text-cyan-100 xl:min-h-[4rem] xl:w-[4rem]"
          >
            {language === "ar" ? "EN" : "AR"}
          </button>
        </div>

        <div
          className="section-surface-muted order-3 col-span-1 min-w-0 rounded-[1.15rem] p-2 xl:col-span-2 2xl:order-2 2xl:col-span-1"
          data-testid="command-ribbon-grid"
        >
          <div className="grid min-w-0 gap-2 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-5">
            {anchorRoutes.map((route) => {
              const Icon = route.icon;
              const isActive = isRouteActive(route.href);
              const translatedLabel = t(route.label);
              const commandLabel = `${translatedLabel} (${route.shortLabel})`;

              return (
                <Link
                  key={route.href}
                  href={route.href}
                  aria-label={commandLabel}
                  title={commandLabel}
                  className={cn(
                    "group industrial-corner relative flex min-h-[4rem] min-w-0 flex-col justify-center overflow-hidden rounded-[1rem] border px-2.5 sm:px-3 text-left transition-all duration-300",
                    isActive
                      ? route.href === "/"
                        ? "border-amber-300/35 bg-[radial-gradient(circle_at_top,rgba(251,191,36,0.18),transparent_60%),linear-gradient(135deg,rgba(30,23,14,0.96),rgba(8,10,14,0.96))] text-white shadow-[0_16px_36px_rgba(120,53,15,0.24)]"
                        : "border-cyan-300/30 bg-[linear-gradient(135deg,rgba(8,30,38,0.94),rgba(8,10,14,0.96))] text-white shadow-[0_16px_36px_rgba(8,145,178,0.18)]"
                      : route.href === "/"
                        ? "border-white/12 bg-[linear-gradient(135deg,rgba(38,31,19,0.92),rgba(8,10,14,0.96))] text-slate-100 hover:border-amber-300/30"
                        : "border-white/10 bg-[linear-gradient(135deg,rgba(10,20,25,0.85),rgba(8,10,14,0.96))] text-slate-200 hover:border-cyan-300/25"
                  )}
                >
                  <div
                    className={cn(
                      "pointer-events-none absolute inset-0 opacity-60 transition-opacity duration-500",
                      route.href === "/" ? "bg-[radial-gradient(circle_at_top_right,rgba(251,191,36,0.12),transparent_42%)]" : "bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.08),transparent_42%)]"
                    )}
                  />
                  <div className="relative flex w-full min-w-0 items-center justify-center gap-2">
                    <div className="flex min-w-0 items-center gap-1.5">
                        <span className="text-[11px] font-black uppercase tracking-[0.08em] text-white whitespace-nowrap">
                          {route.shortLabel}
                        </span>
                        {isActive && (
                          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
                        )}
                    </div>
                    <div className="flex shrink-0 items-center">
                      <div className={cn(
                        "flex size-7 items-center justify-center rounded-[0.65rem] border",
                        route.href === "/" ? "border-amber-200/20 bg-amber-400/10" : "border-cyan-200/20 bg-cyan-400/10"
                      )}>
                        <Icon
                          aria-hidden="true"
                          className={cn(
                            "h-3.5 w-3.5 shrink-0 transition-colors",
                            isActive ? route.color : route.href === "/" ? "text-amber-200" : "text-cyan-200"
                          )}
                        />
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}

            {groupedRoutes.map((group) => {
              const groupHasActiveRoute = group.routes.some((route) => isRouteActive(route.href));

              return (
                <div
                  key={group.id}
                  className="group relative flex min-w-0 flex-col"
                  onMouseEnter={() => setOpenGroupId(group.id)}
                  onMouseLeave={() => setOpenGroupId((current) => current === group.id ? null : current)}
                  onFocusCapture={() => setOpenGroupId(group.id)}
                  onBlur={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                      setOpenGroupId((current) => current === group.id ? null : current);
                    }
                  }}
                >
                  <button
                    type="button"
                    aria-label={`${group.label} navigation group`}
                    aria-expanded={openGroupId === group.id}
                    aria-haspopup="menu"
                    aria-controls={`nav-group-panel-${group.id}`}
                    onClick={() => setOpenGroupId(group.id)}
                    className={cn(
                      "industrial-corner flex min-h-[4rem] w-full min-w-0 flex-col justify-center overflow-hidden rounded-[1rem] border px-2.5 sm:px-3 text-left transition-all duration-300",
                      groupHasActiveRoute
                        ? "border-cyan-300/30 bg-[linear-gradient(135deg,rgba(8,30,38,0.94),rgba(8,10,14,0.96))] text-white shadow-[0_16px_36px_rgba(8,145,178,0.18)]"
                        : "border-white/10 bg-[linear-gradient(135deg,rgba(10,20,25,0.85),rgba(8,10,14,0.96))] text-slate-200 hover:border-cyan-300/25",
                      openGroupId === group.id && "border-amber-300/25 shadow-[0_18px_40px_rgba(120,53,15,0.18)]"
                    )}
                  >
                    <div className="flex w-full min-w-0 items-center justify-center gap-2">
                      <div className="flex min-w-0 items-center gap-1.5">
                          <span className="text-[11px] font-black uppercase tracking-[0.08em] text-white whitespace-nowrap">
                            {group.label}
                          </span>
                          {groupHasActiveRoute && (
                            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
                          )}
                      </div>
                      <div className="flex shrink-0 items-center gap-1">
                        <div className={cn(
                          "flex h-4 min-w-[1.2rem] px-1 items-center justify-center rounded-full text-[9px] font-black uppercase tracking-tight",
                          groupHasActiveRoute ? "bg-cyan-500/20 text-cyan-200" : "bg-white/[0.04] text-slate-500"
                        )}>
                          {group.routes.length}
                        </div>
                        <ChevronDown
                          aria-hidden="true"
                          className={cn(
                            "h-3.5 w-3.5 shrink-0 transition-transform duration-300",
                            openGroupId === group.id ? "rotate-180 text-amber-100" : "text-slate-500"
                          )}
                        />
                      </div>
                    </div>
                  </button>

                  {/* Dropdown Menu */}
                  {openGroupId === group.id ? (
                    <div
                      id={`nav-group-panel-${group.id}`}
                      role="menu"
                      aria-label={`${group.label} routes`}
                      className="absolute left-0 top-full z-[150] w-[min(16.5rem,calc(100vw-1.5rem))] pt-3"
                    >
                      <div className="industrial-corner rounded-[1.35rem] border border-amber-300/12 bg-[linear-gradient(180deg,rgba(22,16,8,0.96),rgba(9,10,14,0.98))] p-3 shadow-[0_28px_90px_rgba(2,6,23,0.82)] backdrop-blur-xl">
                        <div className="border-b border-white/8 px-2 pb-3">
                          <div className="text-[9px] font-black uppercase tracking-[0.32em] text-amber-200/60">
                            Domain Chamber
                          </div>
                          <div className="mt-1 text-[12px] font-black uppercase tracking-[0.24em] text-white">
                            {group.label}
                          </div>
                        </div>
                        <div className="mt-2 flex max-h-[60vh] flex-col gap-1 overflow-y-auto pr-1 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-white/10 hover:[&::-webkit-scrollbar-thumb]:bg-white/20 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-1.5">
                        {group.routes.map((route) => {
                          const translatedLabel = t(route.label);
                          const commandLabel = `${translatedLabel} (${route.shortLabel})`;
                          const isActive = isRouteActive(route.href);
                          const Icon = route.icon;

                          return (
                            <Link
                              key={route.href}
                              href={route.href}
                              aria-label={commandLabel}
                              title={commandLabel}
                              role="menuitem"
                              onClick={() => setOpenGroupId(null)}
                              className={cn(
                                "flex min-w-0 items-center gap-3 rounded-[0.95rem] border px-3 py-2.5 transition",
                                isActive
                                  ? "border-cyan-400/18 bg-cyan-500/10 text-white"
                                  : "border-transparent text-slate-400 hover:border-white/8 hover:bg-white/[0.05] hover:text-slate-100"
                              )}
                            >
                              <div className={cn(
                                "flex size-8 shrink-0 items-center justify-center rounded-lg border",
                                isActive ? "border-cyan-500/30 bg-cyan-500/20" : "border-white/10 bg-black/20"
                              )}>
                                <Icon
                                  aria-hidden="true"
                                  className={cn(
                                    "h-4 w-4 shrink-0 transition-colors",
                                    isActive ? route.color : "text-slate-500",
                                    !isActive && route.hoverColor
                                  )}
                                />
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="truncate text-[11px] font-black uppercase tracking-[0.2em] text-slate-200">
                                  {translatedLabel}
                                </div>
                              </div>
                            </Link>
                          );
                        })}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

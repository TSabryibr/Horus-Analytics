import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type CommandHeaderTone = "primary" | "success" | "warning" | "danger" | "muted" | "info";

export interface CommandHeaderStatusItem {
  label: string;
  value: string;
  tone?: CommandHeaderTone;
}

interface CommandHeaderProps extends HTMLAttributes<HTMLElement> {
  eyebrow?: string;
  title: string;
  description?: string;
  icon?: ReactNode;
  statusItems?: CommandHeaderStatusItem[];
  actions?: ReactNode;
  iconClassName?: string;
}

const statusToneClasses: Record<CommandHeaderTone, string> = {
  primary: "command-chip-primary",
  success: "command-chip-success",
  warning: "command-chip-warning",
  danger: "command-chip-danger",
  muted: "command-chip-muted",
  info: "command-chip-info",
};

export function CommandHeader({
  className,
  eyebrow,
  title,
  description,
  icon,
  statusItems = [],
  actions,
  iconClassName,
  ...props
}: CommandHeaderProps) {
  return (
    <header
      className={cn("section-surface industrial-corner overflow-hidden rounded-[1.75rem]", className)}
      {...props}
    >
      <div className="pointer-events-none absolute inset-x-[16%] top-[-7rem] h-[19rem] rounded-full bg-[radial-gradient(circle,rgba(251,191,36,0.16),transparent_62%)] blur-3xl" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(251,191,36,0.05),transparent_34%),radial-gradient(circle_at_top_right,rgba(34,211,238,0.08),transparent_24%)]" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-amber-300/70 via-cyan-300/18 to-transparent" />
      <div className="relative flex flex-col gap-6 p-6 sm:p-7 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-start gap-4 sm:gap-5">
            {icon ? (
              <div
                className={cn(
                  "flex size-[3.75rem] shrink-0 items-center justify-center rounded-[1.15rem] border border-amber-200/18 bg-[radial-gradient(circle_at_top,rgba(251,191,36,0.18),rgba(34,211,238,0.08)),linear-gradient(180deg,rgba(24,18,12,0.96),rgba(8,13,20,0.92))] text-amber-100 shadow-[0_18px_40px_rgba(120,53,15,0.2)]",
                  iconClassName
                )}
              >
                {icon}
              </div>
            ) : null}

            <div className="min-w-0 flex-1 space-y-3">
              {eyebrow ? <p className="meta-label text-amber-100/60">{eyebrow}</p> : null}
              <div className="space-y-2">
                <h1 className="heading-title text-[clamp(2rem,3.4vw,3.2rem)] font-black tracking-[-0.05em] text-white">
                  {title}
                </h1>
                {description ? (
                  <p className="max-w-3xl text-sm leading-6 text-stone-300/90 sm:text-[15px]">{description}</p>
                ) : null}
              </div>

              {statusItems.length > 0 ? (
                <div className="flex flex-wrap items-center gap-2.5 pt-1">
                  {statusItems.map((item) => (
                    <div
                      key={`${item.label}-${item.value}`}
                      className={cn("command-chip rounded-[999px] bg-black/20", statusToneClasses[item.tone || "muted"])}
                    >
                      <span className="text-[9px] opacity-70">{item.label}</span>
                      <span className="text-[11px] text-current">{item.value}</span>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {actions ? (
          <div className="flex w-full shrink-0 flex-col gap-3 lg:w-auto lg:min-w-[16rem] lg:items-end">
            <div className="section-surface-muted rounded-[1.2rem] border border-white/8 px-3 py-3 lg:min-w-[15rem]">
              <div className="meta-label text-slate-500">Command Actions</div>
              <div className="mt-3 flex w-full flex-col gap-3">{actions}</div>
            </div>
          </div>
        ) : null}
      </div>
    </header>
  );
}

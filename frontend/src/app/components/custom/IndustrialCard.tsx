import React from "react";
import { cn } from "@/lib/utils";

interface IndustrialCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  tone?: "primary" | "secondary" | "rail";
  headerSlot?: React.ReactNode;
  contentClassName?: string;
}

export const IndustrialCard = ({
  className,
  title,
  subtitle,
  tone = "secondary",
  headerSlot,
  contentClassName,
  children,
  ...props
}: IndustrialCardProps) => {
  const toneClasses = {
    primary:
      "border-amber-300/18 bg-[linear-gradient(180deg,rgba(28,20,12,0.96),rgba(10,16,24,0.94)_20%,rgba(2,6,23,0.9))] shadow-[0_30px_90px_rgba(120,53,15,0.2)]",
    secondary:
      "border-white/10 bg-[linear-gradient(180deg,rgba(18,17,15,0.82),rgba(8,13,20,0.88)_24%,rgba(2,6,23,0.86))]",
    rail:
      "border-cyan-300/12 bg-[linear-gradient(180deg,rgba(12,18,31,0.92),rgba(5,14,22,0.92)_22%,rgba(2,6,23,0.82))] backdrop-blur-xl",
  };

  const headerToneClasses = {
    primary: "border-amber-300/15 bg-[linear-gradient(90deg,rgba(251,191,36,0.08),rgba(255,255,255,0.02))]",
    secondary: "border-white/6 bg-[linear-gradient(90deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01))]",
    rail: "border-cyan-300/12 bg-[linear-gradient(90deg,rgba(34,211,238,0.07),rgba(255,255,255,0.01))]",
  };

  const titleToneClasses = {
    primary: "text-amber-100",
    secondary: "text-cyan-200",
    rail: "text-cyan-100",
  };

  return (
    <section
      data-tone={tone}
      className={cn(
        "section-surface industrial-corner flex flex-col",
        toneClasses[tone],
        "industrial-corner",
        className
      )}
      {...props}
    >
      {(title || subtitle || headerSlot) && (
        <div
          className={cn(
            "flex items-start justify-between gap-4 border-b px-4 py-3.5 sm:px-5",
            headerToneClasses[tone]
          )}
        >
          <div className="min-w-0 space-y-1">
            {title && (
              <h3
                className={cn(
                  "heading-title text-[11px] font-black uppercase tracking-[0.22em]",
                  titleToneClasses[tone]
                )}
              >
                {title}
              </h3>
            )}
            {subtitle && <p className="meta-label text-slate-500">{subtitle}</p>}
          </div>
          {headerSlot ?? (
            <div className="flex shrink-0 items-end gap-1.5 opacity-70">
              <div className={cn("h-3 w-1 rounded-full", tone === "primary" ? "bg-amber-300/45" : tone === "rail" ? "bg-cyan-300/30" : "bg-white/20")} />
              <div className={cn("h-4 w-1 rounded-full", tone === "primary" ? "bg-amber-300/25" : tone === "rail" ? "bg-cyan-300/18" : "bg-white/[0.12]")} />
              <div className={cn("h-5 w-1 rounded-full", tone === "primary" ? "bg-amber-300/14" : tone === "rail" ? "bg-cyan-300/12" : "bg-white/8")} />
            </div>
          )}
        </div>
      )}
      <div className={cn("flex-1 p-4 sm:p-5", contentClassName)}>
        {children}
      </div>
    </section>
  );
};

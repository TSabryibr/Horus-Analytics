import React from "react";
import { cn } from "@/lib/utils";

export interface IndustrialInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  shellClassName?: string;
  leadingSlot?: React.ReactNode;
  trailingSlot?: React.ReactNode;
}

export const IndustrialInput = React.forwardRef<HTMLInputElement, IndustrialInputProps>(
  ({ className, shellClassName, leadingSlot, trailingSlot, type, ...props }, ref) => {
    return (
      <div
        className={cn(
          "section-surface-muted industrial-corner group relative flex items-center gap-3 px-3",
          shellClassName
        )}
      >
        {leadingSlot ? (
          <div className="shrink-0 text-slate-500 transition-colors group-focus-within:text-primary">
            {leadingSlot}
          </div>
        ) : null}
        <input
          type={type}
          className={cn(
            "flex h-11 w-full min-w-0 bg-transparent py-3 text-[12px] font-mono tracking-[0.18em] text-slate-100 transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-slate-600 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50",
            className
          )}
          ref={ref}
          {...props}
        />
        {trailingSlot ? (
          <div className="shrink-0 text-slate-500 transition-colors group-focus-within:text-primary">
            {trailingSlot}
          </div>
        ) : null}
        <div className="pointer-events-none absolute bottom-0 left-4 right-4 h-[1px] origin-left scale-x-0 bg-gradient-to-r from-primary/75 via-primary/20 to-transparent transition-transform duration-300 group-focus-within:scale-x-100" />
      </div>
    );
  }
);

IndustrialInput.displayName = "IndustrialInput";

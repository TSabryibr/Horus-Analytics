import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CommandToolbarProps extends HTMLAttributes<HTMLDivElement> {
  label?: string;
  description?: string;
  trailing?: ReactNode;
}

export function CommandToolbar({
  className,
  label,
  description,
  trailing,
  children,
  ...props
}: CommandToolbarProps) {
  return (
    <section
      className={cn("section-surface-muted industrial-corner overflow-hidden rounded-[1.5rem]", className)}
      {...props}
    >
      <div className="flex flex-col gap-4 p-4 sm:p-5">
        {label || description ? (
          <div className="flex flex-col gap-2 border-b border-white/8 pb-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-1">
              {label ? <p className="meta-label text-amber-100/60">{label}</p> : null}
              {description ? <p className="max-w-3xl text-sm text-stone-300/85">{description}</p> : null}
            </div>
            {trailing ? <div className="flex flex-wrap items-center gap-3 lg:justify-end">{trailing}</div> : null}
          </div>
        ) : null}

        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-3">{children}</div>
      </div>
    </section>
  );
}

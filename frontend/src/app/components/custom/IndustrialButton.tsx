import React from "react";
import { cn } from "@/lib/utils";

interface IndustrialButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "alert" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const IndustrialButton = React.forwardRef<HTMLButtonElement, IndustrialButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const variants = {
      primary: "border-primary/35 bg-[linear-gradient(135deg,rgba(34,211,238,0.18),rgba(14,116,144,0.16))] text-cyan-50 hover:border-primary/55 hover:bg-primary/20",
      secondary: "border-white/10 bg-white/[0.04] text-slate-200 hover:border-white/20 hover:bg-white/[0.08]",
      alert: "border-destructive/40 bg-destructive/10 text-rose-200 hover:border-destructive/60 hover:bg-destructive/20",
      ghost: "border-white/10 bg-transparent text-slate-400 hover:border-white/20 hover:bg-white/[0.04] hover:text-slate-100",
    };

    const sizes = {
      sm: "h-9 px-3 text-[10px] tracking-[0.22em]",
      md: "h-10 px-4 text-[10px] tracking-[0.24em]",
      lg: "h-11 px-5 text-[11px] tracking-[0.26em]",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "relative inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[1rem] border font-black uppercase transition-all duration-200 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50",
          "industrial-corner",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

IndustrialButton.displayName = "IndustrialButton";

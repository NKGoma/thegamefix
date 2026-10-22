import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

// Semantic colours are reserved for state: done, paused/warn, failed, running.
const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-zinc-200 text-zinc-600 dark:border-zinc-700 dark:text-zinc-300",
        done: "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400",
        warn: "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400",
        failed: "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400",
        running: "border-blue-500/30 bg-blue-500/10 text-blue-600 dark:text-blue-400",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

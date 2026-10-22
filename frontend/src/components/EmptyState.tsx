import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon: Icon,
  message,
  action,
}: {
  icon: LucideIcon;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-zinc-200 px-6 py-16 text-center dark:border-zinc-800">
      <Icon className="size-8 text-zinc-400" strokeWidth={1.5} />
      <p className="max-w-md text-zinc-500 dark:text-zinc-400">{message}</p>
      {action}
    </div>
  );
}

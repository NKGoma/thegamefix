import { Link } from "react-router-dom";
import { useHealth } from "@/lib/queries";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

export function StatusPill({ collapsed }: { collapsed: boolean }) {
  const { data, isPending, isError } = useHealth();

  let tone: "ok" | "bad" | "pending" = "pending";
  let label = "Checking Ollama…";
  let detail = "Contacting backend";
  if (isError) {
    tone = "bad";
    label = "Backend unreachable";
    detail = "The DelegationLab backend at :8000 is not responding";
  } else if (data) {
    tone = data.ollama.reachable ? "ok" : "bad";
    label = data.ollama.reachable ? "Ollama connected" : "Ollama unreachable";
    detail = data.ollama.reachable
      ? `${data.ollama.url} · v${data.ollama.version ?? "?"}`
      : `${data.ollama.url} — ${data.ollama.error ?? "no response"}`;
  }

  const dot = (
    <span
      className={cn(
        "size-2 shrink-0 rounded-full",
        tone === "ok" && "bg-green-500",
        tone === "bad" && "bg-red-500",
        tone === "pending" && "bg-zinc-400",
        isPending && "animate-pulse",
      )}
    />
  );

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          to="/models"
          data-testid="ollama-status"
          data-state={tone}
          className={cn(
            "flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-900",
            tone === "bad"
              ? "border-red-500/30 text-red-600 dark:text-red-400"
              : "border-zinc-200 text-zinc-600 dark:border-zinc-800 dark:text-zinc-300",
            collapsed && "justify-center px-0",
          )}
        >
          {dot}
          {!collapsed && <span className="truncate">{label}</span>}
        </Link>
      </TooltipTrigger>
      <TooltipContent side="right">{detail}</TooltipContent>
    </Tooltip>
  );
}

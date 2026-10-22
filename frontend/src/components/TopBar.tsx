import { Moon, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { useTheme } from "@/lib/theme";
import { Button } from "./ui/button";

export function TopBar({ title, action }: { title: string; action?: ReactNode }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-zinc-200 bg-white/80 px-6 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <h1 className="text-[20px] font-semibold">{title}</h1>
      <div className="flex items-center gap-2">
        {action}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          data-testid="theme-toggle"
        >
          {theme === "dark" ? <Sun /> : <Moon />}
        </Button>
      </div>
    </header>
  );
}

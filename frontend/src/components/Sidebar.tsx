import { FlaskConical, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { NavLink } from "react-router-dom";
import { footerNav, mainNav, type NavItem } from "@/app/nav";
import { cn } from "@/lib/utils";
import { StatusPill } from "./StatusPill";
import { Button } from "./ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

function NavEntry({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const link = (
    <NavLink
      to={item.path}
      end={item.path === "/"}
      className={({ isActive }) =>
        cn(
          "flex h-9 items-center gap-3 rounded-md px-3 text-sm transition-colors",
          isActive
            ? "bg-zinc-100 font-medium text-zinc-900 dark:bg-zinc-900 dark:text-zinc-50"
            : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100",
          collapsed && "justify-center px-0",
        )
      }
    >
      <item.icon className="size-4 shrink-0" />
      {!collapsed && <span>{item.label}</span>}
    </NavLink>
  );
  if (!collapsed) return link;
  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right">{item.label}</TooltipContent>
    </Tooltip>
  );
}

export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <aside
      data-testid="sidebar"
      data-collapsed={collapsed}
      className={cn(
        "fixed inset-y-0 left-0 z-20 flex flex-col border-r border-zinc-200 bg-zinc-50 transition-[width] duration-150 dark:border-zinc-800 dark:bg-zinc-950",
        collapsed ? "w-14" : "w-60",
      )}
    >
      <div className={cn("flex h-14 items-center gap-2 px-4", collapsed && "justify-center px-0")}>
        <FlaskConical className="size-5 text-indigo-500" />
        {!collapsed && <span className="font-semibold">DelegationLab</span>}
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-2">
        {mainNav.map((item) => (
          <NavEntry key={item.path} item={item} collapsed={collapsed} />
        ))}
      </nav>
      <div className="flex flex-col gap-2 px-2 pb-3">
        {footerNav.map((item) => (
          <NavEntry key={item.path} item={item} collapsed={collapsed} />
        ))}
        <StatusPill collapsed={collapsed} />
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn("justify-start text-zinc-500", collapsed && "justify-center px-0")}
        >
          {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
          {!collapsed && "Collapse"}
        </Button>
      </div>
    </aside>
  );
}

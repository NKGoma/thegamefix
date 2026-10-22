import {
  Bot,
  FlaskConical,
  LayoutDashboard,
  PlayCircle,
  Settings,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
}

export const mainNav: NavItem[] = [
  { path: "/", label: "Overview", icon: LayoutDashboard },
  { path: "/experiments", label: "Experiments", icon: FlaskConical },
  { path: "/runs", label: "Runs", icon: PlayCircle },
  { path: "/personas", label: "Personas", icon: Users },
  { path: "/models", label: "Models", icon: Bot },
];

export const footerNav: NavItem[] = [{ path: "/settings", label: "Settings", icon: Settings }];

export function titleFor(pathname: string): string {
  const item = [...mainNav, ...footerNav].find((n) =>
    n.path === "/" ? pathname === "/" : pathname.startsWith(n.path),
  );
  return item?.label ?? "DelegationLab";
}

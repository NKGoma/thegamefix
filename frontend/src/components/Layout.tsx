import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { titleFor } from "@/app/nav";
import { readStorage, writeStorage } from "@/lib/storage";
import { cn } from "@/lib/utils";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function Layout() {
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState(() => readStorage("dl.sidebar") === "collapsed");

  const toggle = () =>
    setCollapsed((c) => {
      writeStorage("dl.sidebar", c ? "expanded" : "collapsed");
      return !c;
    });

  return (
    <div className="min-h-screen">
      <Sidebar collapsed={collapsed} onToggle={toggle} />
      <div className={cn("transition-[padding] duration-150", collapsed ? "pl-14" : "pl-60")}>
        <TopBar title={titleFor(pathname)} />
        <main className="mx-auto w-full max-w-[1280px] p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

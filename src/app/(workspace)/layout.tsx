"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { CopilotSidebar } from "@copilotkit/react-ui";

const NAV_LINKS = [
  { href: "/", label: "Overview" },
  { href: "/desk", label: "Desk" },
  { href: "/approvals", label: "Approvals" },
];

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <div className="flex-1 flex flex-col">
        <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">AI Employee</p>
              <h1 className="text-lg font-semibold leading-tight">Control Plane Workspace</h1>
              <p className="hidden text-sm text-slate-400 sm:block">
                Monitor queue progress, approvals, and guardrail outcomes as the agent runs.
              </p>
            </div>
            <nav className="flex items-center gap-1 text-sm">
              {NAV_LINKS.map(({ href, label }) => {
                const active = pathname === href || pathname?.startsWith(`${href}/`);
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`rounded-full px-4 py-1.5 transition-colors ${
                      active
                        ? "bg-slate-100 text-slate-900"
                        : "text-slate-300 hover:bg-slate-50/10 hover:text-white"
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-6xl px-6 py-8">{children}</div>
        </main>
      </div>
      <CopilotSidebar
        data-testid="copilot-sidebar"
        clickOutsideToClose={false}
        defaultOpen
        labels={{
          title: "Copilot",
          initial:
            "👋 Need a hand? Ask the control plane agent to draft envelopes, collect evidence, or prep approvals.",
        }}
        className="w-[320px] border-l border-slate-800 bg-slate-900/90 backdrop-blur"
      />
    </div>
  );
}

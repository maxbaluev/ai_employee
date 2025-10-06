"use client";

import { useMemo } from "react";
import { useCoAgent } from "@copilotkit/react-core";

type DeskQueue = Array<{ id: string; status?: string }>;

export default function WorkspaceOverview() {
  const { state } = useCoAgent<{
    desk?: { queue?: DeskQueue };
    approvalModal?: { approvalState?: string | null } | null;
    guardrails?: Record<string, { allowed?: boolean }>;
  }>({
    name: "my_agent",
    initialState: {
      desk: { queue: [] },
      approvalModal: null,
      guardrails: {},
    },
  });

  const queue = state.desk?.queue ?? [];
  const approvals = state.approvalModal ? 1 : 0;
  const blockedGuardrails = useMemo(
    () => Object.values(state.guardrails ?? {}).filter((snapshot) => snapshot?.allowed === false),
    [state.guardrails],
  );

  const approved = queue.filter((item) => item.status === "approved").length;
  const pending = queue.filter((item) => !item.status || item.status === "pending").length;

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-lg shadow-black/20">
        <h1 className="text-3xl font-semibold text-slate-50">Control Plane Overview</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-400">
          This workspace mirrors the shared state emitted by the control plane agent. Keep this page open while
          running the worker or the FastAPI server to observe queue activity, approval requests, and guardrail
          outcomes in real time.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Pending queue items" value={pending} subtitle="Desk > Queue" />
        <MetricCard title="Approvals awaiting review" value={approvals} subtitle="Approvals > Modal" />
        <MetricCard title="Guardrail blocks" value={blockedGuardrails.length} subtitle="Guardrails > Latest run" />
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="text-xl font-semibold text-slate-100">Next steps</h2>
        <ol className="mt-4 space-y-3 text-sm text-slate-300">
          <li>
            <span className="font-semibold text-slate-100">1.</span> Start the control plane locally
            (<code className="mx-1 rounded bg-slate-800 px-2 py-0.5 text-xs">pnpm run dev</code>) and open the Desk to
            watch queue deltas stream in real time.
          </li>
          <li>
            <span className="font-semibold text-slate-100">2.</span> Run the outbox worker with
            <code className="mx-1 rounded bg-slate-800 px-2 py-0.5 text-xs">uv run python -m worker.outbox start</code>
            to execute envelopes and observe status changes in the dashboard.
          </li>
          <li>
            <span className="font-semibold text-slate-100">3.</span> Extend the Approvals surface with custom actions
            or connect Supabase to hydrate historical approvals once Phase 5 begins.
          </li>
        </ol>
      </section>
    </div>
  );
}

function MetricCard({ title, value, subtitle }: { title: string; value: number; subtitle: string }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{subtitle}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-50">{value}</p>
      <p className="text-sm text-slate-400">{title}</p>
    </div>
  );
}

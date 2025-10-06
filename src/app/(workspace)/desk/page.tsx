"use client";

import { useMemo } from "react";
import { useCoAgent } from "@copilotkit/react-core";

type QueueStatus = "pending" | "approved" | "rejected" | string;

type QueueItem = {
  id: string;
  title: string;
  evidence?: string[];
  status?: QueueStatus;
};

type GuardrailSnapshot = Record<
  string,
  {
    allowed?: boolean;
    message?: string;
    [key: string]: unknown;
  }
>;

const STATUS_STYLES: Record<QueueStatus, string> = {
  pending: "bg-amber-500/20 text-amber-200 border border-amber-400/50",
  approved: "bg-emerald-500/15 text-emerald-200 border border-emerald-400/40",
  rejected: "bg-rose-500/15 text-rose-200 border border-rose-400/40",
};

export default function DeskPage() {
  const { state, setState } = useCoAgent<{
    desk?: { queue?: QueueItem[] };
    guardrails?: GuardrailSnapshot;
  }>({
    name: "my_agent",
    initialState: {
      desk: { queue: [] },
      guardrails: {},
    },
  });

  const queue = state.desk?.queue ?? [];
  const guardrails = state.guardrails ?? {};

  const alerts = useMemo(
    () =>
      Object.entries(guardrails)
        .filter(([, snapshot]) => snapshot && snapshot.allowed === false)
        .map(([key, snapshot]) => ({
          key,
          message: snapshot.message ?? "Guardrail blocked this action.",
        })),
    [guardrails],
  );

  const updateStatus = (id: string, status: QueueStatus) => {
    setState((prev) => {
      const queueItems = prev.desk?.queue ?? [];
      const nextQueue = queueItems.map((item) =>
        item.id === id ? { ...item, status } : item,
      );
      return {
        ...prev,
        desk: {
          ...(prev.desk ?? {}),
          queue: nextQueue,
        },
      };
    });
  };

  return (
    <div className="space-y-8">
      {alerts.length > 0 && (
        <section className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-rose-200">
            Guardrail Alerts
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-rose-100">
            {alerts.map((alert) => (
              <li key={alert.key} className="rounded-lg bg-rose-500/10 px-3 py-2">
                <span className="font-semibold capitalize">{alert.key.replace(/([A-Z])/g, " $1").trim()}:</span> {alert.message}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Tenant Desk Queue</h2>
            <p className="text-sm text-slate-400">
              These queue items reflect the latest state shared by the control plane agent.
            </p>
          </div>
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
            {queue.length} item{queue.length === 1 ? "" : "s"}
          </span>
        </header>

        {queue.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {queue.map((item) => (
              <QueueCard key={item.id} item={item} onUpdateStatus={updateStatus} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function QueueCard({
  item,
  onUpdateStatus,
}: {
  item: QueueItem;
  onUpdateStatus: (id: string, status: QueueStatus) => void;
}) {
  const statusLabel = (item.status ?? "pending").replace(/_/g, " ");
  const chipClasses = STATUS_STYLES[item.status ?? "pending"] ?? STATUS_STYLES.pending;

  return (
    <article className="flex h-full flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/20 transition hover:border-slate-700">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">{item.title}</h3>
            <p className="text-xs uppercase tracking-wide text-slate-500">Envelope {item.id}</p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${chipClasses}`}>
            {statusLabel}
          </span>
        </div>

        {item.evidence && item.evidence.length > 0 && (
          <ul className="space-y-2 text-sm text-slate-300">
            {item.evidence.map((evidence, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="mt-1 h-2 w-2 rounded-full bg-slate-500" aria-hidden />
                <span>{evidence}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-5 flex flex-wrap gap-2 text-xs">
        <button
          type="button"
          onClick={() => onUpdateStatus(item.id, "approved")}
          className="rounded-full bg-emerald-500/20 px-4 py-1 font-semibold text-emerald-200 transition hover:bg-emerald-500/30"
        >
          Mark approved
        </button>
        <button
          type="button"
          onClick={() => onUpdateStatus(item.id, "rejected")}
          className="rounded-full bg-rose-500/20 px-4 py-1 font-semibold text-rose-200 transition hover:bg-rose-500/30"
        >
          Flag for follow-up
        </button>
        <button
          type="button"
          onClick={() => onUpdateStatus(item.id, "pending")}
          className="rounded-full border border-slate-600 px-4 py-1 font-semibold text-slate-200 transition hover:border-slate-400"
        >
          Reset
        </button>
      </div>
    </article>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-12 text-center">
      <h3 className="text-lg font-semibold text-slate-200">Queue is quiet</h3>
      <p className="mt-2 text-sm text-slate-400">
        Ask the agent to draft a new envelope or sync your objectives to populate the desk.
      </p>
    </div>
  );
}

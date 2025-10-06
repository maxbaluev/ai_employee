"use client";

import { useMemo } from "react";
import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";

type ApprovalAction = {
  label: string;
  action: string;
  variant?: "primary" | "secondary" | "destructive" | "ghost" | string;
};

type ApprovalModalState = {
  envelopeId: string;
  proposal: {
    summary: string;
    evidence: string[];
  };
  requiredScopes: string[];
  approvalState: "pending" | "authorized" | "denied" | "cancelled" | string;
  schema?: {
    properties?: Record<string, { title?: string; description?: string; type?: string }>;
  };
  uiSchema?: Record<string, unknown>;
  formData?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  actions: Record<"approve" | "reject" | "cancel", ApprovalAction> & Record<string, ApprovalAction>;
  lastUpdated?: string;
};

const VARIANT_STYLES: Record<string, string> = {
  primary: "bg-emerald-500 text-emerald-950 hover:bg-emerald-400",
  secondary: "bg-slate-100/10 text-slate-100 hover:bg-slate-100/20",
  destructive: "bg-rose-500/20 text-rose-200 hover:bg-rose-500/30",
  ghost: "border border-slate-600 text-slate-200 hover:border-slate-400",
};

export default function ApprovalsPage() {
  const { state, setState } = useCoAgent<{ approvalModal?: ApprovalModalState | null }>({
    name: "my_agent",
    initialState: {
      approvalModal: null,
    },
  });

  const modal = state.approvalModal ?? null;

  useCopilotAction({ name: "approvals:approve", available: "disabled" });
  useCopilotAction({ name: "approvals:reject", available: "disabled" });
  useCopilotAction({ name: "approvals:cancel", available: "disabled" });

  const schemaFields = useMemo(() => {
    if (!modal?.schema?.properties) return [] as Array<{ key: string; title: string; type?: string }>;
    return Object.entries(modal.schema.properties).map(([key, schema]) => ({
      key,
      title: schema.title ?? key,
      type: schema.type,
    }));
  }, [modal]);

  const updateFormField = (key: string, value: unknown) => {
    setState((prev) => {
      const current = prev.approvalModal;
      if (!current) return prev;
      return {
        ...prev,
        approvalModal: {
          ...current,
          formData: {
            ...(current.formData ?? {}),
            [key]: value,
          },
          lastUpdated: new Date().toISOString(),
        },
      };
    });
  };

  const updateState = (nextState: ApprovalModalState["approvalState"]) => {
    setState((prev) => {
      const current = prev.approvalModal;
      if (!current) return prev;
      return {
        ...prev,
        approvalModal: {
          ...current,
          approvalState: nextState,
          lastUpdated: new Date().toISOString(),
        },
      };
    });
  };

  if (!modal) {
    return <EmptyApprovalsState />;
  }

  const { proposal, requiredScopes, approvalState, formData, actions } = modal;

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
      <section className="space-y-6">
        <header className="space-y-2">
          <span className="text-xs uppercase tracking-[0.3em] text-slate-500">Envelope {modal.envelopeId}</span>
          <h2 className="text-3xl font-semibold text-slate-50">{proposal.summary}</h2>
          <p className="text-sm text-slate-400">
            Review the supporting evidence, confirm the form inputs, and approve or reject the agent&apos;s proposal.
          </p>
        </header>

        <section aria-labelledby="evidence-heading" className="space-y-3">
          <div className="flex items-center gap-3">
            <h3 id="evidence-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-300">
              Supporting Evidence
            </h3>
            <span className="text-xs text-slate-500">{proposal.evidence.length} item{proposal.evidence.length === 1 ? "" : "s"}</span>
          </div>
          <ul className="space-y-2 text-sm text-slate-200">
            {proposal.evidence.map((item, idx) => (
              <li key={idx} className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3">
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="form-heading" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 id="form-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-300">
              Approval Details
            </h3>
            <StatusPill state={approvalState} />
          </div>

          {schemaFields.length === 0 ? (
            <p className="rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-6 text-sm text-slate-400">
              No schema fields provided for this approval. The agent may be requesting a simple acknowledgement.
            </p>
          ) : (
            <div className="space-y-4">
              {schemaFields.map(({ key, title }) => (
                <label key={key} className="block space-y-2 text-sm text-slate-200">
                  <span className="font-medium">{title}</span>
                  <textarea
                    rows={4}
                    defaultValue={formData?.[key] as string | undefined}
                    onChange={(event) => updateFormField(key, event.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-slate-400"
                    placeholder="Add context for the reviewer"
                  />
                </label>
              ))}
            </div>
          )}
        </section>
      </section>

      <aside className="space-y-6">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Required Scopes</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {requiredScopes.length === 0 ? (
              <span className="rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300">
                No additional scopes
              </span>
            ) : (
              requiredScopes.map((scope) => (
                <span key={scope} className="rounded-full bg-amber-500/15 px-3 py-1 text-xs font-medium text-amber-200">
                  {scope}
                </span>
              ))
            )}
          </div>
        </section>

        {modal.metadata && Object.keys(modal.metadata).length > 0 && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Metadata</h3>
            <dl className="mt-3 space-y-2 text-xs text-slate-300">
              {Object.entries(modal.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between gap-3">
                  <dt className="text-slate-500">{key}</dt>
                  <dd className="font-mono text-slate-200">{String(value)}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Actions</h3>
          <p className="mt-2 text-xs text-slate-400">
            Actions notify the agent via shared state today. Hook into CopilotKit actions once backend endpoints are live.
          </p>
          <div className="mt-4 grid gap-2">
            {Object.entries(actions).map(([key, config]) => (
              <button
                key={key}
                type="button"
                onClick={() => updateState(key === "approve" ? "authorized" : key === "reject" ? "denied" : "cancelled")}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  VARIANT_STYLES[config.variant ?? "primary"] ?? VARIANT_STYLES.primary
                }`}
              >
                {config.label}
              </button>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}

function StatusPill({ state }: { state: ApprovalModalState["approvalState"] }) {
  const style =
    state === "authorized"
      ? "bg-emerald-500/20 text-emerald-200 border border-emerald-400/40"
      : state === "denied"
      ? "bg-rose-500/20 text-rose-200 border border-rose-400/40"
      : state === "cancelled"
      ? "bg-slate-500/20 text-slate-200 border border-slate-400/40"
      : "bg-amber-500/20 text-amber-200 border border-amber-400/40";

  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${style}`}>
      {state}
    </span>
  );
}

function EmptyApprovalsState() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-12 text-center">
      <h2 className="text-xl font-semibold text-slate-200">No approvals pending</h2>
      <p className="mt-2 text-sm text-slate-400">
        When the agent queues an envelope that needs human review, the schema-driven form will appear here.
      </p>
    </div>
  );
}

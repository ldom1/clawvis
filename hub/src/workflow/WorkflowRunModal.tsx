import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { WorkflowView } from "./WorkflowView";
import type { JobNodeData, JobStatus } from "./types";

interface LogEvent {
  ts?: string;
  component?: string;
  event?: string;
  name?: string;
  workflow?: string;
  job?: string;
  failed_job?: string;
  jobs?: string[];
  error?: string;
  result_chars?: number;
  level?: string;
  trace_id?: string;
  [k: string]: unknown;
}

interface DerivedState {
  statuses: Record<string, JobStatus>;
  durations: Record<string, number>;
  errors: Record<string, string>;
  current: string | null;
  done: boolean;
  failed: boolean;
}

const POLL_INTERVAL_MS = 2000;
const POLL_DEADLINE_MS = 10 * 60 * 1000;

function deriveState(
  workflowName: string,
  orderedJobs: string[],
  events: LogEvent[],
  sinceMs: number,
): DerivedState {
  const statuses: Record<string, JobStatus> = {};
  const durations: Record<string, number> = {};
  const errors: Record<string, string> = {};
  for (const id of orderedJobs) statuses[id] = "pending";

  const sorted = [...events].sort((a, b) => {
    const ta = a.ts ? Date.parse(a.ts) : 0;
    const tb = b.ts ? Date.parse(b.ts) : 0;
    return ta - tb;
  });

  let current: string | null = null;
  let triggered = false;
  let done = false;
  let failed = false;
  const jobStarts: Record<string, number> = {};

  for (const e of sorted) {
    const ts = e.ts ? Date.parse(e.ts) : 0;
    if (ts < sinceMs) continue;
    const comp = e.component ?? "";
    const ev = e.event ?? "";

    if (comp === "scheduler.workflow") {
      const wf = e.workflow ?? e.name;
      if (wf !== workflowName) continue;
      if (ev === "workflow.trigger") {
        triggered = true;
        current = orderedJobs[0] ?? null;
        if (current && statuses[current] === "pending") {
          statuses[current] = "running";
          jobStarts[current] = ts;
        }
      } else if (ev === "workflow.job_done" && e.job) {
        if (statuses[e.job] !== undefined) {
          statuses[e.job] = "success";
          const start = jobStarts[e.job];
          if (start) durations[e.job] = ts - start;
        }
        const idx = orderedJobs.indexOf(e.job);
        const next = idx >= 0 ? orderedJobs[idx + 1] : undefined;
        if (next) {
          current = next;
          if (statuses[next] === "pending") {
            statuses[next] = "running";
            jobStarts[next] = ts;
          }
        } else {
          current = null;
        }
      } else if (ev === "workflow.stopped" && e.failed_job) {
        if (statuses[e.failed_job] !== undefined) {
          statuses[e.failed_job] = "failed";
          if (typeof e.error === "string") errors[e.failed_job] = e.error;
          const start = jobStarts[e.failed_job];
          if (start) durations[e.failed_job] = ts - start;
        }
        const idx = orderedJobs.indexOf(e.failed_job);
        for (let i = idx + 1; i < orderedJobs.length; i++) {
          const id = orderedJobs[i]!;
          if (statuses[id] === "pending") statuses[id] = "skipped";
        }
        failed = true;
        done = true;
        current = null;
      } else if (ev === "workflow.complete") {
        done = true;
        for (const id of orderedJobs) {
          if (statuses[id] === "pending" || statuses[id] === "running") {
            statuses[id] = "success";
          }
        }
        current = null;
      } else if (ev === "workflow.invalid_payload") {
        failed = true;
        done = true;
      }
    } else if (comp === "scheduler.job" && typeof e.name === "string") {
      if (!triggered) continue;
      if (statuses[e.name] === undefined) continue;
      if (ev === "agent.request.error") {
        if (typeof e.error === "string") errors[e.name] = e.error;
      }
    }
  }

  return { statuses, durations, errors, current, done, failed };
}

export interface WorkflowRunModalProps {
  workflowName: string;
  orderedJobs: string[];
  sinceIso: string;
  fr?: boolean;
  onClose: () => void;
}

export function WorkflowRunModal({
  workflowName,
  orderedJobs,
  sinceIso,
  fr = false,
  onClose,
}: WorkflowRunModalProps) {
  const sinceMs = useMemo(
    () => new Date(sinceIso).getTime() - 2000,
    [sinceIso],
  );
  const [events, setEvents] = useState<LogEvent[]>([]);
  const [timedOut, setTimedOut] = useState(false);
  const deadlineRef = useRef<number>(Date.now() + POLL_DEADLINE_MS);
  const stoppedRef = useRef(false);

  const state = useMemo(
    () => deriveState(workflowName, orderedJobs, events, sinceMs),
    [workflowName, orderedJobs, events, sinceMs],
  );

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      if (cancelled || stoppedRef.current) return;
      try {
        const res = await fetch("/api/hub/kanban/logs?limit=200");
        if (res.ok) {
          const data = (await res.json()) as { logs?: LogEvent[] };
          const fresh = (data.logs ?? []).filter((e) => {
            const comp = e.component ?? "";
            const ts = e.ts ? Date.parse(e.ts) : 0;
            if (ts < sinceMs) return false;
            if (comp === "scheduler.workflow") {
              return (e.workflow ?? e.name) === workflowName;
            }
            if (comp === "scheduler.job" && typeof e.name === "string") {
              return orderedJobs.includes(e.name);
            }
            return false;
          });
          if (!cancelled) setEvents(fresh.reverse());
        }
      } catch {
        /* network error — retry next tick */
      }
      if (Date.now() > deadlineRef.current) {
        stoppedRef.current = true;
        if (!cancelled) setTimedOut(true);
        return;
      }
      if (cancelled || stoppedRef.current) return;
      timer = window.setTimeout(poll, POLL_INTERVAL_MS);
    };

    poll();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [workflowName, orderedJobs, sinceMs]);

  useEffect(() => {
    if (state.done) {
      stoppedRef.current = true;
    }
  }, [state.done]);

  const nodeData: Record<string, Partial<JobNodeData>> = useMemo(() => {
    const out: Record<string, Partial<JobNodeData>> = {};
    for (const id of orderedJobs) {
      out[id] = {
        label: id,
        status: state.statuses[id] ?? "pending",
        duration: state.durations[id] ?? null,
        error: state.errors[id] ?? null,
        isCurrent: id === state.current,
      };
    }
    return out;
  }, [orderedJobs, state]);

  const edges = useMemo(
    () =>
      orderedJobs.slice(0, -1).map((source, i) => ({
        source,
        target: orderedJobs[i + 1]!,
      })),
    [orderedJobs],
  );

  const onKey = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  const statusBadge = (() => {
    if (timedOut) {
      return (
        <span className="wf-modal-badge warn">
          {fr ? "Délai dépassé" : "Timed out"}
        </span>
      );
    }
    if (state.failed) {
      return (
        <span className="wf-modal-badge error">
          {fr ? "Échec ✗" : "Failed ✗"}
        </span>
      );
    }
    if (state.done) {
      return (
        <span className="wf-modal-badge ok">
          {fr ? "Terminé ✓" : "Done ✓"}
        </span>
      );
    }
    return (
      <span className="wf-modal-badge running">
        <span className="cron-spinner" /> {fr ? "En cours…" : "Running…"}
      </span>
    );
  })();

  return (
    <div
      className="modal-overlay open"
      role="dialog"
      aria-modal="true"
      onKeyDown={onKey}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="panel wf-run-modal-panel">
        <button
          type="button"
          className="modal-close"
          onClick={onClose}
          aria-label={fr ? "Fermer" : "Close"}
        >
          ×
        </button>
        <div className="wf-run-modal-header">
          <h2 className="cron-modal-title">▶ {workflowName}</h2>
          {statusBadge}
        </div>
        <div className="wf-run-modal-body">
          <WorkflowView
            nodeIds={orderedJobs}
            edges={edges}
            nodeData={nodeData}
            isExecuting={!state.done && !timedOut}
            height={420}
            fr={fr}
          />
        </div>
        <div className="cron-modal-footer wf-run-modal-footer">
          <a
            href={`/logs/?search=${encodeURIComponent(workflowName)}`}
            className="btn btn-compact"
          >
            {fr ? "Voir les logs →" : "View logs →"}
          </a>
          <button type="button" className="btn btn-compact" onClick={onClose}>
            {fr ? "Fermer" : "Close"}
          </button>
        </div>
      </div>
    </div>
  );
}

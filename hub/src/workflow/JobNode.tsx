import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { JobFlowNode, JobStatus } from "./types";

const STATUS_LABEL: Record<JobStatus, string> = {
  idle: "—",
  pending: "Pending",
  running: "Running",
  success: "Success",
  failed: "Failed",
  skipped: "Skipped",
};

const STATUS_DOT: Record<JobStatus, string> = {
  idle: "wf-dot-idle",
  pending: "wf-dot-pending",
  running: "wf-dot-running",
  success: "wf-dot-success",
  failed: "wf-dot-failed",
  skipped: "wf-dot-skipped",
};

function formatDuration(ms?: number | null): string | null {
  if (ms == null || !Number.isFinite(ms) || ms < 0) return null;
  if (ms < 1000) return `${Math.round(ms)} ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)} s`;
  const m = Math.floor(s / 60);
  const rem = Math.round(s - m * 60);
  return `${m}m ${rem}s`;
}

function JobNodeComponent({ data, selected }: NodeProps<JobFlowNode>) {
  const status = data.status ?? "idle";
  const duration = formatDuration(data.duration);
  const subtitle =
    duration ??
    (data.schedule && data.schedule !== "manual" ? data.schedule : null) ??
    (data.enabled === false ? "disabled" : null);

  const classes = [
    "wf-job-node",
    `wf-job-node-${status}`,
    selected ? "wf-job-node-selected" : "",
    data.isCurrent ? "wf-job-node-current" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={classes}
      title={data.error ? `${data.label} — ${data.error}` : data.label}
    >
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={false}
        className="wf-handle"
      />
      <div className="wf-job-node-row">
        <span className={`wf-job-node-dot ${STATUS_DOT[status]}`} aria-hidden />
        <span className="wf-job-node-label">{data.label}</span>
      </div>
      <div className="wf-job-node-meta">
        <span className="wf-job-node-status">{STATUS_LABEL[status]}</span>
        {subtitle ? (
          <span className="wf-job-node-sub" title={subtitle}>
            {subtitle}
          </span>
        ) : null}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={false}
        className="wf-handle"
      />
    </div>
  );
}

export const JobNode = memo(JobNodeComponent);
JobNode.displayName = "JobNode";

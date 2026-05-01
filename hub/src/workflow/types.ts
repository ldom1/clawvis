import type { Node, Edge } from "@xyflow/react";

export type JobStatus =
  | "idle"
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "skipped";

export interface JobNodeData extends Record<string, unknown> {
  label: string;
  status: JobStatus;
  schedule?: string | null;
  enabled?: boolean;
  nextRun?: string | null;
  duration?: number | null;
  error?: string | null;
  isCurrent?: boolean;
}

export type JobFlowNode = Node<JobNodeData, "jobNode">;
export type JobFlowEdge = Edge;

export interface WorkflowGraphInput {
  /** Ordered list of node ids (job names). */
  nodeIds: string[];
  /** Optional explicit edges. If omitted, no edges are drawn. */
  edges?: Array<{ source: string; target: string }>;
  /** Optional per-node data (status, schedule, etc.). */
  nodeData?: Record<string, Partial<JobNodeData>>;
}

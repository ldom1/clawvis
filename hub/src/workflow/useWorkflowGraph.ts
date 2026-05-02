import { useMemo } from "react";
import { MarkerType } from "@xyflow/react";
import { layoutGraph, type LayoutDirection } from "./layout";
import type {
  JobFlowEdge,
  JobFlowNode,
  JobNodeData,
  WorkflowGraphInput,
} from "./types";

export interface UseWorkflowGraphResult {
  nodes: JobFlowNode[];
  edges: JobFlowEdge[];
  isReady: boolean;
  hasCycle: boolean;
  hasDuplicates: boolean;
}

function detectCycle(
  nodeIds: string[],
  edges: Array<{ source: string; target: string }>,
): boolean {
  const adj = new Map<string, string[]>();
  for (const id of nodeIds) adj.set(id, []);
  for (const e of edges) {
    if (!adj.has(e.source)) adj.set(e.source, []);
    adj.get(e.source)!.push(e.target);
  }
  const WHITE = 0;
  const GRAY = 1;
  const BLACK = 2;
  const color = new Map<string, number>();
  for (const id of adj.keys()) color.set(id, WHITE);
  const stack: Array<[string, number]> = [];
  for (const start of adj.keys()) {
    if (color.get(start) !== WHITE) continue;
    stack.push([start, 0]);
    while (stack.length) {
      const top = stack[stack.length - 1]!;
      const [node, idx] = top;
      if (idx === 0) color.set(node, GRAY);
      const neighbors = adj.get(node) ?? [];
      if (idx >= neighbors.length) {
        color.set(node, BLACK);
        stack.pop();
        continue;
      }
      top[1] = idx + 1;
      const next = neighbors[idx]!;
      const c = color.get(next);
      if (c === GRAY) return true;
      if (c === WHITE) stack.push([next, 0]);
    }
  }
  return false;
}

export function useWorkflowGraph(
  input: WorkflowGraphInput,
  options: { direction?: LayoutDirection; animateRunning?: boolean } = {},
): UseWorkflowGraphResult {
  const { direction = "LR", animateRunning = false } = options;
  const { nodeIds, edges: rawEdges, nodeData } = input;

  return useMemo(() => {
    const seen = new Set<string>();
    const dedupedIds: string[] = [];
    let hasDuplicates = false;
    for (const id of nodeIds) {
      if (seen.has(id)) {
        hasDuplicates = true;
        continue;
      }
      seen.add(id);
      dedupedIds.push(id);
    }

    const safeEdges = (rawEdges ?? []).filter(
      (e) => seen.has(e.source) && seen.has(e.target) && e.source !== e.target,
    );

    const hasCycle = detectCycle(dedupedIds, safeEdges);
    const usableEdges = hasCycle ? [] : safeEdges;

    const baseNodes: JobFlowNode[] = dedupedIds.map((id) => {
      const extra = nodeData?.[id] ?? {};
      const data: JobNodeData = {
        label: extra.label ?? id,
        status: extra.status ?? "idle",
        ...extra,
      };
      return {
        id,
        type: "jobNode",
        position: { x: 0, y: 0 },
        data,
        draggable: false,
        selectable: true,
        connectable: false,
      };
    });

    const baseEdges: JobFlowEdge[] = usableEdges.map((e) => {
      const targetData = nodeData?.[e.target];
      const sourceData = nodeData?.[e.source];
      const targetStatus = targetData?.status ?? "idle";
      const sourceStatus = sourceData?.status ?? "idle";
      const isActive =
        animateRunning &&
        (sourceStatus === "running" ||
          targetStatus === "running" ||
          (sourceStatus === "success" && targetStatus === "pending"));
      const isDone = sourceStatus === "success" && targetStatus === "success";
      const isFailed = sourceStatus === "failed" || targetStatus === "failed";

      let className = "wf-edge";
      if (isActive) className += " wf-edge-active";
      else if (isDone) className += " wf-edge-done";
      else if (isFailed) className += " wf-edge-failed";
      else className += " wf-edge-pending";

      return {
        id: `${e.source}->${e.target}`,
        source: e.source,
        target: e.target,
        animated: isActive,
        className,
        markerEnd: { type: MarkerType.ArrowClosed },
      };
    });

    const laid = layoutGraph(baseNodes, baseEdges, direction);
    return {
      nodes: laid.nodes,
      edges: laid.edges,
      isReady: dedupedIds.length > 0,
      hasCycle,
      hasDuplicates,
    };
  }, [nodeIds, rawEdges, nodeData, direction, animateRunning]);
}

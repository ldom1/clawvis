import dagre from "dagre";
import type { JobFlowEdge, JobFlowNode } from "./types";

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

export type LayoutDirection = "LR" | "TB";

export interface LayoutResult {
  nodes: JobFlowNode[];
  edges: JobFlowEdge[];
}

/**
 * Layout nodes/edges with dagre. When edges are empty we fall back to a grid
 * so isolated jobs don't collapse on top of each other.
 */
export function layoutGraph(
  nodes: JobFlowNode[],
  edges: JobFlowEdge[],
  direction: LayoutDirection = "LR",
): LayoutResult {
  if (nodes.length === 0) return { nodes, edges };

  if (edges.length === 0) {
    const cols = Math.max(1, Math.ceil(Math.sqrt(nodes.length)));
    const gapX = NODE_WIDTH + 60;
    const gapY = NODE_HEIGHT + 40;
    const positioned = nodes.map((n, i) => ({
      ...n,
      position: { x: (i % cols) * gapX, y: Math.floor(i / cols) * gapY },
      sourcePosition: direction === "LR" ? ("right" as const) : ("bottom" as const),
      targetPosition: direction === "LR" ? ("left" as const) : ("top" as const),
    }));
    return { nodes: positioned, edges };
  }

  const g = new dagre.graphlib.Graph();
  g.setGraph({
    rankdir: direction,
    nodesep: 40,
    ranksep: 80,
    marginx: 20,
    marginy: 20,
  });
  g.setDefaultEdgeLabel(() => ({}));

  for (const n of nodes) {
    g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const e of edges) {
    g.setEdge(e.source, e.target);
  }
  dagre.layout(g);

  const positioned = nodes.map((n) => {
    const { x, y } = g.node(n.id) ?? { x: 0, y: 0 };
    return {
      ...n,
      position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 },
      sourcePosition: direction === "LR" ? ("right" as const) : ("bottom" as const),
      targetPosition: direction === "LR" ? ("left" as const) : ("top" as const),
    };
  });

  return { nodes: positioned, edges };
}

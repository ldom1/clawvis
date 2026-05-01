import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type ColorMode,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { JobNode } from "./JobNode";
import { useWorkflowGraph } from "./useWorkflowGraph";
import type { JobFlowNode, WorkflowGraphInput } from "./types";

const NODE_TYPES: NodeTypes = { jobNode: JobNode };
const MINIMAP_THRESHOLD = 8;

export interface WorkflowViewProps extends WorkflowGraphInput {
  /** Triggers running-job UX (pulsing border, animated edges, auto-pan). */
  isExecuting?: boolean;
  /** Container height; defaults to 360px. */
  height?: string | number;
  /** Empty state copy when no jobs are provided. */
  emptyLabel?: string;
  /** Direction of the layout. Defaults to LR. */
  direction?: "LR" | "TB";
  /** Optional locale flag for warning copy. */
  fr?: boolean;
}

function detectColorMode(): ColorMode {
  if (typeof document === "undefined") return "dark";
  return document.body.classList.contains("theme-light") ? "light" : "dark";
}

function FitOnChange({ nodes }: { nodes: JobFlowNode[] }) {
  const { fitView } = useReactFlow();
  useEffect(() => {
    if (!nodes.length) return;
    const id = window.requestAnimationFrame(() => {
      fitView({ padding: 0.18, duration: 250 });
    });
    return () => window.cancelAnimationFrame(id);
  }, [nodes.length, fitView]);
  return null;
}

function PanToCurrent({ nodes }: { nodes: JobFlowNode[] }) {
  const { setCenter, getZoom } = useReactFlow();
  const currentId = useMemo(() => {
    const running = nodes.find((n) => n.data.status === "running");
    if (running) return running.id;
    const current = nodes.find((n) => n.data.isCurrent);
    return current?.id ?? null;
  }, [nodes]);
  useEffect(() => {
    if (!currentId) return;
    const target = nodes.find((n) => n.id === currentId);
    if (!target) return;
    const x = target.position.x + 100;
    const y = target.position.y + 40;
    setCenter(x, y, { zoom: getZoom(), duration: 400 });
  }, [currentId, nodes, setCenter, getZoom]);
  return null;
}

function WorkflowViewInner(props: WorkflowViewProps) {
  const {
    nodeIds,
    edges,
    nodeData,
    isExecuting = false,
    height = 360,
    emptyLabel,
    direction = "LR",
    fr = false,
  } = props;

  const { nodes, edges: flowEdges, isReady, hasCycle, hasDuplicates } =
    useWorkflowGraph(
      { nodeIds, edges, nodeData },
      { direction, animateRunning: isExecuting },
    );

  const [colorMode, setColorMode] = useState<ColorMode>(() => detectColorMode());
  useEffect(() => {
    if (typeof document === "undefined") return;
    const observer = new MutationObserver(() => setColorMode(detectColorMode()));
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);

  const showMiniMap = nodeIds.length >= MINIMAP_THRESHOLD;

  if (!isReady) {
    return (
      <div className="wf-empty" style={{ height }}>
        <p className="muted" style={{ fontSize: 13 }}>
          {emptyLabel ?? (fr ? "Aucun job à afficher." : "No jobs to display.")}
        </p>
      </div>
    );
  }

  return (
    <div className="wf-canvas-wrap" style={{ height }}>
      {hasCycle ? (
        <div className="wf-warning wf-warning-error">
          {fr
            ? "Cycle détecté dans le workflow — graphe désactivé."
            : "Cycle detected in workflow — graph disabled."}
        </div>
      ) : null}
      {hasDuplicates ? (
        <div className="wf-warning">
          {fr
            ? "Jobs en double dans le pipeline — affichés une seule fois."
            : "Duplicate jobs in pipeline — shown once."}
        </div>
      ) : null}
      <ReactFlow
        nodes={nodes}
        edges={flowEdges}
        nodeTypes={NODE_TYPES}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        zoomOnScroll
        panOnScroll={false}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        proOptions={{ hideAttribution: true }}
        colorMode={colorMode}
        minZoom={0.4}
        maxZoom={1.6}
      >
        <Background gap={18} size={1} />
        <Controls showInteractive={false} />
        {showMiniMap ? (
          <MiniMap pannable zoomable className="wf-minimap" />
        ) : null}
        <FitOnChange nodes={nodes} />
        {isExecuting ? <PanToCurrent nodes={nodes} /> : null}
      </ReactFlow>
    </div>
  );
}

export function WorkflowView(props: WorkflowViewProps) {
  return (
    <ReactFlowProvider>
      <WorkflowViewInner {...props} />
    </ReactFlowProvider>
  );
}

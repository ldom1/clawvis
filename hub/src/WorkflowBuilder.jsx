import React, { useState, useCallback } from "react";
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

export default function WorkflowBuilder({ jobs, onSave, onCancel, fr }) {
  const initialNodes = jobs.map((job, i) => ({
    id: job.name,
    data: { label: job.name },
    position: { x: 160, y: 60 + i * 90 },
  }));

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [name, setName] = useState("");
  const [cron, setCron] = useState("");
  const [isManual, setIsManual] = useState(false);
  const [tz, setTz] = useState("UTC");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const onConnect = useCallback(
    (params) => {
      const sourceHasOutgoing = edges.some((e) => e.source === params.source);
      const targetHasIncoming = edges.some((e) => e.target === params.target);
      if (sourceHasOutgoing || targetHasIncoming) return;
      setEdges((eds) =>
        addEdge(
          { ...params, markerEnd: { type: MarkerType.ArrowClosed } },
          eds,
        ),
      );
    },
    [edges],
  );

  function deriveJobOrder() {
    if (!edges.length) return [];
    const targets = new Set(edges.map((e) => e.target));
    const root = edges.find((e) => !targets.has(e.source))?.source;
    if (!root) return [];
    const order = [root];
    let current = root;
    for (let i = 0; i < edges.length; i++) {
      const next = edges.find((e) => e.source === current);
      if (!next) break;
      order.push(next.target);
      current = next.target;
    }
    return order;
  }

  async function handleSave() {
    setError("");
    if (!name.trim()) {
      setError(fr ? "Le nom est requis." : "Name is required.");
      return;
    }
    const jobOrder = deriveJobOrder();
    if (jobOrder.length < 2) {
      setError(
        fr
          ? "Connectez au moins 2 jobs pour former un workflow."
          : "Connect at least 2 jobs to form a workflow.",
      );
      return;
    }
    setSaving(true);
    try {
      await onSave({
        name: name.trim(),
        jobs: jobOrder,
        cron: isManual ? null : cron.trim() || null,
        timezone: tz.trim() || "UTC",
        enabled: true,
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "flex", height: "100%", gap: 16, padding: 16 }}>
      <div
        style={{
          flex: 1,
          border: "1px solid #333",
          borderRadius: 8,
          overflow: "hidden",
          background: "#1a1a2e",
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          colorMode="dark"
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
      <div
        style={{
          width: 220,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        <div className="field">
          <label>{fr ? "Nom" : "Name"}</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="my-workflow"
          />
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
          <input
            type="checkbox"
            checked={isManual}
            onChange={(e) => setIsManual(e.target.checked)}
          />
          {fr ? "Manuel uniquement" : "Manual only"}
        </label>
        {!isManual && (
          <div className="field">
            <label>Cron</label>
            <input
              value={cron}
              onChange={(e) => setCron(e.target.value)}
              placeholder="0 9 * * *"
            />
          </div>
        )}
        <div className="field">
          <label>Timezone</label>
          <input
            value={tz}
            onChange={(e) => setTz(e.target.value)}
            placeholder="UTC"
          />
        </div>
        {error && (
          <p style={{ color: "#ef4444", fontSize: 12, margin: 0 }}>{error}</p>
        )}
        <div style={{ display: "flex", gap: 8, marginTop: "auto" }}>
          <button
            className="btn btn-primary btn-compact"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "…" : fr ? "Enregistrer" : "Save"}
          </button>
          <button className="btn btn-compact" onClick={onCancel}>
            {fr ? "Annuler" : "Cancel"}
          </button>
        </div>
      </div>
    </div>
  );
}

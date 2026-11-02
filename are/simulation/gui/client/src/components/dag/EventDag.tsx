// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Stack } from "@mui/material";
import { Edge, MarkerType, Node } from "@xyflow/react";
import * as React from "react";
import { useEffect, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { ARESimulationEvent } from "../../utils/types";
import ScenarioDebugView from "../scenarios/debug/ScenarioDebugView";
import FlowDag from "./FlowDag";
import { NodeSelectionProvider } from "./NodeSelectionContext";

/**
 * Recursively adds events to a Directed Acyclic Graph (DAG) structure.
 *
 * @param nodes - A record of nodes in the DAG, indexed by node ID.
 * @param edges - A record of edges in the DAG, indexed by edge ID.
 * @param events - A readonly array of ARESimulationEvent objects to be added to the DAG.
 * @param parent - The parent node to which the current event node will be connected, or null if it is a root node.
 */
function addToDag(
  nodes: Record<string, Node>,
  edges: Record<string, Edge>,
  events: ReadonlyArray<ARESimulationEvent>,
  parentId: string | null,
) {
  events.forEach((event) => {
    const eventId = event.event_id;

    if (parentId) {
      const edgeId = `${parentId}>${eventId}`;
      if (!edges[edgeId]) {
        edges[edgeId] = {
          id: edgeId,
          source: String(parentId),
          target: String(eventId),
          markerEnd: { type: MarkerType.ArrowClosed },
          type: "floating",
        };
      }
    }

    if (!nodes[eventId]) {
      nodes[eventId] = {
        id: eventId,
        type: "EventNode",
        data: {
          event: event,
          nodeClass: "event-node-" + event.event_type.toLowerCase(),
        },
        position: { x: 0, y: 0 },
      };

      addToDag(nodes, edges, event.successors, eventId);
    }
    return;
  });
}

function EventDag({
  events,
}: {
  events: ReadonlyArray<ARESimulationEvent> | null;
}): React.ReactNode {
  const { scenario } = useAppContext();
  const [isScenarioInitialized, setIsScenarioInitialized] = useState(false);
  const [nodes, setNodes] = useState<Array<Node>>([]);
  const [edges, setEdges] = useState<Array<Edge>>([]);
  const comment = scenario?.comment;

  useEffect(() => {
    if (events === null) {
      return;
    }
    // Construct a DAG of events.
    const updatedNodes: Record<string, Node> = {};
    const updatedEdges: Record<string, Edge> = {};
    addToDag(updatedNodes, updatedEdges, events, null);
    if (comment) {
      updatedNodes["comment"] = {
        id: "comment",
        type: "CommentNode",
        data: {
          comment,
        },
        position: { x: 0, y: 0 },
      };
    }
    setNodes(Object.values(updatedNodes));
    setEdges(Object.values(updatedEdges));
  }, [events, setNodes, setEdges, comment]);

  useEffect(() => {
    if (events === null || isScenarioInitialized) {
      return;
    }
    setIsScenarioInitialized(true);
  }, [events, isScenarioInitialized]);

  let flowDag = (
    <FlowDag
      nodez={nodes}
      edgez={edges}
      isScenarioInitialized={isScenarioInitialized}
    />
  );
  let scenarioDebugView = <ScenarioDebugView />;
  let eventEditor = null;

  return (
    <NodeSelectionProvider>
      <div style={{ position: "relative", height: "100%" }}>
        <Stack direction="row" spacing={1} height={"100%"}>
          <Stack width={"100%"}>
            {flowDag}
            {scenarioDebugView}
          </Stack>
          {eventEditor}
        </Stack>
      </div>
    </NodeSelectionProvider>
  );
}

export default EventDag;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import Dagre from "@dagrejs/dagre";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { alpha, useTheme } from "@mui/material";
import {
  Background,
  BackgroundVariant,
  ControlButton,
  Controls,
  Edge,
  MiniMap,
  Node,
  NodeChange,
  ReactFlow,
  useEdgesState,
  useNodesInitialized,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useScenarioDebugContext } from "../../contexts/ScenarioDebugContext";
import CommentNode, { COMMENT_NODE_BACKGROUND_COLOR } from "./CommentNode";
import "./dag.css";
import EventNode from "./EventNode";
import FloatingEdge from "./FloatingEdge";
import GetStartedWithMessage from "./GetStartedWithMessage";
import { useNodeSelection } from "./NodeSelectionContext";

export const FIT_VIEW_OPTIONS = { padding: 0.25, duration: 200 };

const getLayoutedElements = (
  nodes: ReadonlyArray<Node>,
  edges: ReadonlyArray<Edge>,
  options: { direction: string },
  defaultWidth: number = 400,
  defaultHeight: number = 200,
) => {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: options.direction });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? defaultWidth,
      height: node.measured?.height ?? defaultHeight,
    }),
  );

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? defaultWidth) / 2;
      const y = position.y - (node.measured?.height ?? defaultHeight) / 2;

      return { ...node, position: { x, y } };
    }),
    edges: [...edges],
  };
};

export interface FlowDagProps {
  nodez: ReadonlyArray<Node>;
  edgez: ReadonlyArray<Edge>;
  isScenarioInitialized: boolean;
  hasMargin?: boolean;
}

/**
 * FlowDag component renders a directed acyclic graph (DAG) of events using ReactFlow.
 * It handles layout, navigation, and interaction with the graph.
 *
 * @param {FlowDagProps} props - Component props
 * @returns {JSX.Element} The rendered FlowDag component
 */
function FlowDag({
  nodez,
  edgez,
  isScenarioInitialized,
  hasMargin,
}: FlowDagProps) {
  const theme = useTheme();
  const { scenario, isLoadingScenario } = useAppContext();
  // Preliminary layout to get DAG nodes' sizes, etc.
  const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
    nodez,
    edgez,
    { direction: "LR" },
  );
  const isNodesInitialized = useNodesInitialized();
  const [isDagInitialized, setIsDagInitialized] = useState(false);
  const { fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);
  const { selectNode, selectedNodeId } = useNodeSelection();
  const { isDebugViewOpen, setIsDebugViewOpen } = useScenarioDebugContext();
  const [showMiniMap, setShowMiniMap] = useState(false);
  const miniMapTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [currentScenarioId, setCurrentScenarioId] = useState(
    scenario?.scenarioId,
  );
  const isEmptyScenario = scenario && nodez.length === 0;

  // Apply predefined layout.
  const onLayout = useCallback(
    (direction: string) => {
      const layouted = getLayoutedElements(nodes, edges, { direction });
      setNodes([...layouted.nodes]);
      setEdges([...layouted.edges]);
    },
    [nodes, edges, setNodes, setEdges],
  );

  function djb2Hash(str: string) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = (hash << 5) + hash + str.charCodeAt(i);
    }
    return hash;
  }

  const prevDagHash = useRef(0);
  useEffect(() => {
    const dagHash = djb2Hash(JSON.stringify(nodez));
    if (prevDagHash.current !== dagHash) {
      const newLayouted = getLayoutedElements(nodez, edgez, {
        direction: "LR",
      });
      setNodes([...newLayouted.nodes]);
      setEdges([...newLayouted.edges]);
      prevDagHash.current = dagHash;
    }
    // Don't include other fields in the dependency array
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodez]);

  useEffect(() => {
    if (isNodesInitialized && !isDagInitialized) {
      onLayout("LR");
      fitView(FIT_VIEW_OPTIONS);
      setIsDagInitialized(true);
    }
  }, [
    isNodesInitialized,
    isDagInitialized,
    setIsDagInitialized,
    onLayout,
    fitView,
  ]);

  useEffect(() => {
    if (isLoadingScenario) {
      setIsDagInitialized(false);
    }
  }, [isLoadingScenario]);

  useEffect(() => {
    if (scenario) {
      setTimeout(() => {
        fitView(FIT_VIEW_OPTIONS);
      }, 200);
    }
  }, [fitView, scenario, isDebugViewOpen]);

  const handleNodesChange = useCallback(
    (changes: NodeChange<Node>[]) => {
      onNodesChange(changes);
      if (scenario && scenario.scenarioId !== currentScenarioId) {
        fitView(FIT_VIEW_OPTIONS);
        setCurrentScenarioId(scenario.scenarioId);
      }
    },
    [fitView, scenario, currentScenarioId, onNodesChange],
  );

  const handleMoveEnd = useCallback(() => {
    if (miniMapTimeoutRef.current) {
      clearTimeout(miniMapTimeoutRef.current);
    }
    miniMapTimeoutRef.current = setTimeout(() => {
      setShowMiniMap(false);
    }, 500);
  }, [miniMapTimeoutRef]);

  const handleMoveStart = useCallback(() => {
    if (miniMapTimeoutRef.current) {
      clearTimeout(miniMapTimeoutRef.current);
    }
    setShowMiniMap(true);
  }, [miniMapTimeoutRef]);

  let getStartedWithMessage = <GetStartedWithMessage />;
  let flowDagActions = null;

  useEffect(() => {
    setIsDebugViewOpen(!isEmptyScenario);
  }, [isEmptyScenario, setIsDebugViewOpen]);

  return (
    <motion.div
      style={{
        width: "100%",
        height: "100%",
        maxWidth: "100%",
        position: "relative",
      }}
      initial={{ opacity: 0 }}
      animate={{
        opacity: 1,
        overflow: "hidden",
        borderRadius: hasMargin ? "0 12px 12px 0" : "0",
        marginBottom: hasMargin ? "8px" : "0",
        boxShadow: theme.shadows[6],
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={onEdgesChange}
        colorMode="dark"
        nodeTypes={{ EventNode: EventNode, CommentNode: CommentNode }}
        edgeTypes={{ floating: FloatingEdge }}
        fitView
        minZoom={0.1}
        onPaneClick={() => {
          selectNode(null);
        }}
        onMoveStart={handleMoveStart}
        onMoveEnd={handleMoveEnd}
        attributionPosition="bottom-left"
        elementsSelectable
      >
        <Controls
          position="bottom-right"
          fitViewOptions={FIT_VIEW_OPTIONS}
          style={{
            boxShadow: theme.shadows[3],
          }}
        >
          <ControlButton onClick={() => onLayout("LR")} title="horizontal">
            <ArrowForwardIcon />
          </ControlButton>
          <ControlButton onClick={() => onLayout("TB")} title="vertical">
            <ArrowDownwardIcon />
          </ControlButton>
        </Controls>
        <Background
          variant={BackgroundVariant.Dots}
          gap={16}
          size={1}
          bgColor={theme.palette.background.default}
          color={theme.palette.text.secondary}
        />
        {flowDagActions}
        <motion.div animate={{ opacity: nodes.length && showMiniMap ? 1 : 0 }}>
          <MiniMap
            position="bottom-right"
            pannable
            style={{
              marginRight: "60px",
              borderRadius: theme.shape.borderRadius,
              overflow: "hidden",
              boxShadow: theme.shadows[6],
            }}
            nodeBorderRadius={12}
            nodeColor={(node) => {
              if (node.type === "CommentNode") {
                return alpha(COMMENT_NODE_BACKGROUND_COLOR, 0.5);
              } else {
                return node.id === selectedNodeId
                  ? theme.palette.action.active
                  : theme.palette.action.disabled;
              }
            }}
          />
        </motion.div>
      </ReactFlow>
      {isScenarioInitialized && isEmptyScenario && getStartedWithMessage}
    </motion.div>
  );
}

export default FlowDag;

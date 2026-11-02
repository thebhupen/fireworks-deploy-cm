// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { createContext, ReactNode, useContext, useState } from "react";

type NodeSelectionContextType = {
  selectedNodeId: string | null;
  highlightedNodeId: string | null;
  selectNode: (nodeId: string | null) => void;
  highlightNode: (nodeId: string | null) => void;
};

const NodeSelectionContext = createContext<
  NodeSelectionContextType | undefined
>(undefined);

export const NodeSelectionProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(
    null,
  );

  const selectNode = (nodeId: string | null) => {
    setSelectedNodeId(nodeId);
  };

  const highlightNode = (nodeId: string | null) => {
    setHighlightedNodeId(nodeId);
  };

  return (
    <NodeSelectionContext.Provider
      value={{ selectedNodeId, selectNode, highlightedNodeId, highlightNode }}
    >
      {children}
    </NodeSelectionContext.Provider>
  );
};

export const useNodeSelection = () => {
  const context = useContext(NodeSelectionContext);
  if (!context) {
    throw new Error(
      "useNodeSelection must be used within a NodeSelectionProvider",
    );
  }
  return context;
};

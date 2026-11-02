// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { createContext, ReactNode, useContext, useState } from "react";

type ScenarioDebugContextType = {
  isDebugViewOpen: boolean;
  setIsDebugViewOpen: (isDebugViewOpen: boolean) => void;
};

const ScenarioDebugContext = createContext<
  ScenarioDebugContextType | undefined
>(undefined);

export const ScenarioDebugProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [isDebugViewOpen, setIsDebugViewOpen] = useState(false);

  return (
    <ScenarioDebugContext.Provider
      value={{ isDebugViewOpen, setIsDebugViewOpen }}
    >
      {children}
    </ScenarioDebugContext.Provider>
  );
};

export const useScenarioDebugContext = () => {
  const context = useContext(ScenarioDebugContext);
  if (!context) {
    throw new Error(
      "useScenarioDebugContext must be used within a ScenarioDebugProvider",
    );
  }
  return context;
};

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React, { createContext, useContext, useState } from "react";

export type Tabs = "agent-chat" | "agent-logs" | "annotated-chat";

export interface TabsContextType {
  selectedTab: Tabs;
  setSelectedTab: (tab: Tabs) => void;
}

const TabsContext = createContext<TabsContextType>({
  selectedTab: "agent-chat",
  setSelectedTab: () => {},
});

interface TabsContextProviderProps {
  children: React.ReactNode;
  initialTab?: Tabs;
}

/**
 * TabsContextProvider is a React functional component that provides
 * a context for managing tab state within the playground view.
 * It maintains the currently selected tab and provides a function to update it.
 *
 * @param {TabsContextProviderProps} props - The props for the component,
 * including children and an optional initial tab value.
 *
 * @returns {JSX.Element} The provider component that wraps its children with
 * the TabsContext.
 */
const TabsContextProvider: React.FC<TabsContextProviderProps> = ({
  children,
  initialTab = "agent-chat",
}) => {
  const [selectedTab, setSelectedTab] = useState<Tabs>(initialTab);

  return (
    <TabsContext.Provider
      value={{
        selectedTab,
        setSelectedTab,
      }}
    >
      {children}
    </TabsContext.Provider>
  );
};

export const useTabs = () => {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error("useTabs must be used within a TabsContextProvider");
  }
  return context;
};

export default TabsContextProvider;

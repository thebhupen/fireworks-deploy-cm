// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import { Container, Tab } from "@mui/material";
import { useEffect, useState } from "react";

export interface TabProps {
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: TabProps[];
  initialSelectedTab?: string;
  resetSelectedTabOnUpdate?: boolean;
}

/**
 * Tabs component that renders a set of tabs with their respective content.
 *
 * @param tabs - Array of tab objects containing label and content.
 * @param initialSelectedTab - Optional initial tab to be selected.
 * @param resetSelectedTabOnUpdate - Optional flag to reset the selected tab when the tabs prop changes.
 *
 * @returns A JSX element containing the tab navigation and content panels.
 */
export const Tabs = ({
  tabs,
  initialSelectedTab,
  resetSelectedTabOnUpdate,
}: TabsProps) => {
  // Wrap the tabs and selectedTab in a single state to avoid out-of-sync updates.
  const [tabsData, setTabsData] = useState<{
    tabs: TabProps[];
    selectedTab: string;
  }>({ tabs: tabs, selectedTab: initialSelectedTab ?? tabs[0]?.label ?? "" });

  useEffect(() => {
    if (resetSelectedTabOnUpdate) {
      setTabsData({
        tabs: tabs,
        selectedTab: initialSelectedTab ?? tabs[0]?.label ?? "",
      });
    } else {
      setTabsData({ ...tabsData, tabs: tabs });
    }
  }, [tabs]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: string) => {
    setTabsData({ ...tabsData, selectedTab: newValue });
  };

  return (
    <TabContext value={tabsData.selectedTab}>
      <Container maxWidth={false}>
        <TabList
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: "divider" }}
        >
          {tabsData.tabs.map((tab, index) => (
            <Tab key={index} label={tab.label} value={tab.label} />
          ))}
        </TabList>
      </Container>
      {tabsData.tabs.map((tab, index) => (
        <TabPanel key={index} value={tab.label}>
          {tab.content}
        </TabPanel>
      ))}
    </TabContext>
  );
};

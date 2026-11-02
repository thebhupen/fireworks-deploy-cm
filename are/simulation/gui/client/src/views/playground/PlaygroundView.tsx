// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";

import { ChatSection } from "../../components/user-agent-dialog/ChatSection";

import PageLayout, { TabsState } from "../../components/layout/PageLayout";

import IntegrationInstructionsIcon from "@mui/icons-material/IntegrationInstructions";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { Stack, useTheme } from "@mui/material";
import { AgentLogsSection } from "../../components/agent-logs/AgentLogsSection";
import { ChatInput } from "../../components/user-agent-dialog/ChatInput";
import { PlaygroundChatHeader } from "../../components/user-agent-dialog/PlaygroundChatHeader";
import { useAppContext } from "../../contexts/AppContextProvider";
import { Tabs, useTabs } from "../../contexts/TabsContextProvider";

function PlaygroundView(): React.ReactNode {
  const { worldLogs } = useAppContext();
  const { selectedTab, setSelectedTab } = useTabs();
  const theme = useTheme();

  const tabs: TabsState<Tabs> = {
    all: [
      {
        id: "agent-chat",
        label: "Agent chat",
        icon: <SmartToyIcon fontSize="small" />,
      },
      {
        id: "agent-logs",
        label: "Agent logs",
        icon: <IntegrationInstructionsIcon fontSize="small" />,
      },
    ],
    selected: selectedTab,
    setSelected: setSelectedTab,
  };

  let tabContent = null;
  let subagentSidebar = null;

  if (selectedTab === "agent-chat") {
    let header = <PlaygroundChatHeader />;

    tabContent = (
      <Stack
        direction="row"
        sx={{
          flexGrow: 1,
          overflow: "hidden",
          borderLeft: `1px solid ${theme}`,
        }}
      >
        <ChatSection input={<ChatInput />} header={header} />
        {subagentSidebar}
      </Stack>
    );
  } else if (selectedTab === "agent-logs") {
    tabContent = <AgentLogsSection key="agent-logs" worldLogs={worldLogs} />;
  }

  return <PageLayout tabs={tabs}>{tabContent}</PageLayout>;
}

export default PlaygroundView;

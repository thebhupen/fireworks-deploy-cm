// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import IntegrationInstructionsIcon from "@mui/icons-material/IntegrationInstructions";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import * as React from "react";
import { useState } from "react";
import { AgentLogsSection } from "../../components/agent-logs/AgentLogsSection";
import PageLayout, { TabsState } from "../../components/layout/PageLayout";
import { ChatInput } from "../../components/user-agent-dialog/ChatInput";
import { ChatSection } from "../../components/user-agent-dialog/ChatSection";
import { PlaygroundChatHeader } from "../../components/user-agent-dialog/PlaygroundChatHeader";
import { useAppContext } from "../../contexts/AppContextProvider";

export type Tabs = "agent-chat" | "agent-logs" | "annotated-chat";

function ArenaView(): React.ReactNode {
  const { worldLogs } = useAppContext();
  const urlParams = new URLSearchParams(window.location.search);
  const groupId = urlParams.get("group_id");
  const [selectedTab, setSelectedTab] = useState<Tabs>(
    groupId != null ? "annotated-chat" : "agent-chat",
  );

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

  if (selectedTab === "agent-chat") {
    tabContent = (
      <ChatSection input={<ChatInput />} header={<PlaygroundChatHeader />} />
    );
  } else if (selectedTab === "agent-logs") {
    tabContent = <AgentLogsSection key="agent-logs" worldLogs={worldLogs} />;
  }

  return <PageLayout tabs={tabs}>{tabContent}</PageLayout>;
}

export default ArenaView;

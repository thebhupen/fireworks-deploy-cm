// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";

import PageLayout from "../../components/layout/PageLayout";

import { AgentLogsSection } from "../../components/agent-logs/AgentLogsSection";
import { useAppContext } from "../../contexts/AppContextProvider";

export default function AgentLogsView(): React.ReactNode {
  const { worldLogs } = useAppContext();
  return (
    <PageLayout>
      <AgentLogsSection worldLogs={worldLogs} />
    </PageLayout>
  );
}

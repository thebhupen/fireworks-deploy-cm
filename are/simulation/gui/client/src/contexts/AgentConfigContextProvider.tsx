// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React, { useState } from "react";

export interface AgentConfigContextType {
  agent: string | null;
  setAgent: (agent: string | null) => void;
  agents: Array<string>;
  setAgents: (agents: Array<string>) => void;
  agentConfig: any;
  setAgentConfig: (config: any) => void;
}

/**
 * Context to propagate agent's configuration throughout the UI.
 */
export const AgentConfigContext =
  React.createContext<AgentConfigContextType | null>(null);

interface AgentConfigContextProviderProps {
  children: React.ReactNode;
  value?: Partial<AgentConfigContextType>;
}

const AgentConfigContextProvider: React.FC<AgentConfigContextProviderProps> = ({
  children,
  value,
}) => {
  const [agent, setAgent] = useState<string | null>(value?.agent ?? null);
  const [agents, setAgents] = useState<Array<string>>(value?.agents ?? []);

  const [agentConfig, setAgentConfig] = useState<any>(
    value?.agentConfig ?? null,
  );

  return (
    <AgentConfigContext.Provider
      value={{
        agent,
        setAgent,
        agents,
        setAgents,
        agentConfig,
        setAgentConfig,
      }}
    >
      {children}
    </AgentConfigContext.Provider>
  );
};

export const useAgentConfigContext = () =>
  React.useContext(AgentConfigContext) as AgentConfigContextType;

export const updateAgentConfigField = (
  agentConfig: any,
  configPath: string,
  value: any,
) => {
  // Deep copy the config.
  let updatedAgentConfig = JSON.parse(JSON.stringify(agentConfig));
  let nodeToUpdate = updatedAgentConfig.value;
  const parts = configPath.split(".");
  const key = parts.pop();
  for (const part of parts) {
    if (nodeToUpdate === undefined || nodeToUpdate === null) {
      return null;
    }
    nodeToUpdate = nodeToUpdate[part];
  }
  if (
    nodeToUpdate === undefined ||
    nodeToUpdate === null ||
    key === undefined ||
    key === null
  ) {
    return null;
  }
  // Replace the value in the particular path of the config object
  // and send the update to the server.
  nodeToUpdate[key] = value;
  return updatedAgentConfig;
};

export default AgentConfigContextProvider;

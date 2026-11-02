// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import { EnvState } from "../utils/types";
import { useAppContext } from "./AppContextProvider";

// Type for pending messages
export interface PendingMessage {
  id: string;
  content: string;
  attachments: string[];
  timestamp: number;
  correlationId: string | null;
}

interface PendingMessagesContextType {
  pendingMessages: PendingMessage[];
  addPendingMessage: (message: PendingMessage) => void;
  removePendingMessage: (id: string) => void;
  updatePendingMessageCorrelationKey: (
    id: string,
    correlationId: string,
  ) => void;
  clearAllPendingMessages: () => void;
}

const PendingMessagesContext = createContext<PendingMessagesContextType | null>(
  null,
);

export const usePendingMessages = () => {
  const context = useContext(PendingMessagesContext);
  if (!context) {
    throw new Error(
      "usePendingMessages must be used within a PendingMessagesProvider",
    );
  }
  return context;
};

interface PendingMessagesProviderProps {
  children: ReactNode;
}

export const PendingMessagesProvider: React.FC<
  PendingMessagesProviderProps
> = ({ children }) => {
  const [pendingMessages, setPendingMessages] = useState<PendingMessage[]>([]);
  const { envState } = useAppContext();

  // Clear all pending messages when environment stops or resets
  useEffect(() => {
    if (envState === EnvState.STOPPED || envState === EnvState.SETUP) {
      setPendingMessages([]);
    }
  }, [envState]);

  const addPendingMessage = (message: PendingMessage) => {
    setPendingMessages((prev) => [...prev, message]);
  };

  const removePendingMessage = (id: string) => {
    setPendingMessages((prev) => prev.filter((message) => message.id !== id));
  };

  const updatePendingMessageCorrelationKey = (
    id: string,
    correlationId: string,
  ) => {
    setPendingMessages((prev) =>
      prev.map((message) =>
        message.id === id ? { ...message, correlationId } : message,
      ),
    );
  };

  const clearAllPendingMessages = () => {
    setPendingMessages([]);
  };

  return (
    <PendingMessagesContext.Provider
      value={{
        pendingMessages,
        addPendingMessage,
        removePendingMessage,
        updatePendingMessageCorrelationKey,
        clearAllPendingMessages,
      }}
    >
      {children}
    </PendingMessagesContext.Provider>
  );
};

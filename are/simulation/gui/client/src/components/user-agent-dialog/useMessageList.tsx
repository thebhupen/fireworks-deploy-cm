// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useMemo } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { usePendingMessages } from "../../contexts/PendingMessagesContext";
import {
  AgentUserMessage,
  createMessageList,
  Message,
  Notification,
} from "./createMessageList";

export function useMessageList(): {
  messages: ReadonlyArray<Message>;
  notifications: ReadonlyArray<Notification>;
} {
  const { eventLog, worldLogs, appsState, infoLevel } = useAppContext();
  const { pendingMessages } = usePendingMessages();

  // Create the message list from event log and world logs
  const { messages, notifications } = useMemo(() => {
    return createMessageList({
      appsState,
      eventLog,
      worldLogs,
      infoLevel,
    });
  }, [eventLog, worldLogs, appsState, infoLevel]);

  // Create pending message objects and combine with regular messages
  const allMessages = useMemo(() => {
    // Convert pending messages to AgentUserMessage format
    const pendingUserMessages: AgentUserMessage[] = pendingMessages.map(
      (pending) => ({
        type: "AgentUserMessage",
        id: pending.id,
        sender: "User",
        content: pending.content,
        timestamp: pending.timestamp,
        time_read: pending.timestamp,
        attachments: pending.attachments,
        isPending: true, // Add a flag to identify pending messages
        correlationId: pending.correlationId || undefined, // Add the correlationId from the pending message, convert null to undefined
      }),
    );

    // Filter out pending messages that have already been processed
    // This is a backup to the correlation-based matching in ChatInput.tsx
    const filteredPendingMessages = pendingUserMessages.filter((pendingMsg) => {
      // If the message has a correlationId, check if there's a real message with the same correlationId in the event log
      if (pendingMsg.correlationId) {
        return !eventLog.some(
          (event) =>
            // Check if the pending message correlationId matches the return value in the event metadata
            event.metadata?.return_value === pendingMsg.correlationId,
        );
      }
      // If no correlationId, fall back to ID-based matching
      return !eventLog.some(
        (event) =>
          // Check if the pending message ID matches the return value in the event metadata
          event.metadata?.return_value === pendingMsg.id,
      );
    });

    // Combine regular messages with pending messages
    return [...filteredPendingMessages, ...messages];
  }, [messages, pendingMessages, eventLog]);

  return { messages: allMessages, notifications };
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import type { JSONType } from "../../components/JSONView";
import {
  AgentLog,
  AppName,
  ARESimulationEventAction,
  ARESimulationEventType,
  EventLog,
  ToolMetadataType,
} from "../../utils/types";

import { IMAGE_EXTENSION_REGEX } from "../../utils/fileUtils";
import { WebNavStream } from "../webnav/WebNav";
import { InfoLevel } from "./InfoLevelMenu";

export type Message =
  | GroupMessageType
  | ObservationMessageType
  | ImageMessageType
  | DocumentMessageType
  | ErrorMessage
  | AgentUserMessage
  | ActionMessageType
  | ThoughtMessageType
  | WebNavMessageType
  | FactsMessageType
  | PlanMessageType
  | LLMInputOutputType;

export type Notification = ActionMessageType;

export type Sender = "User" | "Agent";

export type AgentUserMessage = {
  type: "AgentUserMessage";
  id: string;
  sender: Sender;
  content: string;
  time_read: number;
  timestamp: number;
  attachments: string[];
  isPending?: boolean; // Flag to indicate if this is a pending message
  correlationId?: string; // Key to correlate this message with a response
};

export type ObservationMessageType = {
  type: "OBSERVATION";
  id: string;
  content: string;
  timestamp: number;
  attachments: ObservationMessageAttachmentType[];
};

export type ObservationMessageAttachmentType = {
  path: string;
  mime_type: string;
};

export type GroupType = "STEP" | "INIT" | "SUBAGENT" | "ROOT" | "UNKNOWN";

export type GroupMessageType = {
  type: "GROUP";
  id: string;
  messages: Array<Message>;
  groupType: GroupType;
  depth: number;
  groupId: string | null;
  timestamp: number;
};

export type ErrorMessage = {
  type: "ERROR";
  id: string;
  content: string;
  error: string;
  timestamp: number;
};

export type ActionMessageType = {
  type: "ACTION";
  id: string;
  content: string;
  sender: string;
  timestamp: number;
  appName: AppName;
  actionName: string | undefined;
  input: JSONType;
  output: JSONType | null;
  exception: string | null;
  exceptionStackTrace: string | null;
  completed: boolean;
  toolMetadata?: ToolMetadataType;
};

export type ThoughtMessageType = {
  type: "THOUGHT";
  id: string;
  sender: "AGENT";
  timestamp: number;
  content: string;
};

export type FactsMessageType = {
  type: "FACTS";
  id: string;
  sender: "AGENT";
  timestamp: number;
  content: string;
};

export type PlanMessageType = {
  type: "PLAN";
  id: string;
  sender: "AGENT";
  timestamp: number;
  content: string;
};

export type LLMInputOutputType = {
  type: "LLMInputOutput";
  id: string;
  sender: "AGENT";
  timestamp: number;
  input: string;
  output: string | null;
  duration: number | null;
};

export type WebNavMessageType = {
  type: "WebNavigation";
  id: string;
  sender: "AGENT";
  timestamp: number;
  stream: WebNavStream;
};

export type ImageMessageType = {
  type: "Image";
  id: string;
  sender: Sender;
  timestamp: number;
  src: string;
};

export type DocumentMessageType = {
  type: "Document";
  id: string;
  sender: Sender;
  timestamp: number;
  src: string;
};

export type EnvironmentNotificationType = {
  type: "EnvironmentNotification";
  content: string;
  timestamp: number;
  id: string;
};

export function createMessageList({
  appsState,
  worldLogs,
  eventLog,
  infoLevel,
}: {
  appsState: Array<{ app_name: string; queries: any }>;
  worldLogs: ReadonlyArray<AgentLog>;
  eventLog: EventLog;
  infoLevel: InfoLevel;
}): {
  messages: ReadonlyArray<Message>;
  notifications: ReadonlyArray<Notification>;
} {
  const messages: Array<Message> = [];
  const notifications: Array<Notification> = [];

  for (const event of eventLog) {
    if (
      ["Files", "SandboxLocalFileSystem"].includes(event.action.app_name) &&
      event.action.function_name === "display"
    ) {
      if (IMAGE_EXTENSION_REGEX.test(event.action.args.path)) {
        const imageMessage: ImageMessageType = {
          id: event.event_time!.toString(),
          type: "Image",
          sender: "Agent",
          timestamp: event.event_time!,
          src: event.action.args.path,
        };

        messages.push(imageMessage);
      } else {
        const documentMessage: DocumentMessageType = {
          id: event.event_time!.toString(),
          type: "Document",
          sender: "Agent",
          timestamp: event.event_time!,
          src: event.action.args.path,
        };

        messages.push(documentMessage);
      }
    } else {
      if (
        event.action.app_name === "AgentUserInterface" &&
        event.action.function_name === "send_message_to_user"
      ) {
        const agentUserMessage: AgentUserMessage = {
          type: "AgentUserMessage",
          id: event.event_id.toString(),
          sender: "Agent",
          time_read: event.event_time ?? 0,
          timestamp: event.event_time ?? 0,
          content:
            event.action.resolved_args?.content ??
            event.action.args?.content ??
            "ERROR",
          attachments:
            event.action.resolved_args?.attachments ??
            event.action.args?.attachments ??
            [],
        };

        messages.push(agentUserMessage);
      } else if (
        event.action.app_name === "AgentUserInterface" &&
        event.action.function_name === "send_message_to_agent"
      ) {
        const agentUserMessage: AgentUserMessage = {
          type: "AgentUserMessage",
          id: event.metadata.return_value ?? event.event_id.toString(),
          correlationId: event.metadata.return_value ?? undefined,
          sender: "User",
          time_read: event.event_time ?? 0,
          timestamp: event.event_time ?? 0,
          content:
            event.action.resolved_args?.content ??
            event.action.args?.content ??
            "ERROR",
          attachments:
            event.action.resolved_args?.attachments ??
            event.action.args?.attachments ??
            [],
        };

        messages.push(agentUserMessage);
      } else if (
        event.event_type === ARESimulationEventType.Agent ||
        event.event_type === ARESimulationEventType.User ||
        event.event_type === ARESimulationEventType.Env
      ) {
        // Add type assertion for event.action to include tool_metadata
        const action = event.action as ARESimulationEventAction;
        const actionMessage: ActionMessageType = {
          id: event.event_id.toString(),
          content: "",
          type: "ACTION",
          sender: event.event_type,
          timestamp: event.event_time ?? 0,
          appName: event.action.app_name as AppName,
          actionName: event.action.function_name,
          input: event.action.args,
          output: event.metadata.return_value ?? null,
          exception: event.metadata.exception ?? null,
          exceptionStackTrace: event.metadata.exception_stack_trace ?? null,
          completed: event.metadata.completed,
        };

        // Add tool metadata if available
        if (action.tool_metadata) {
          actionMessage["actionName"] = action.tool_metadata.name;
          actionMessage.toolMetadata = {
            name: action.tool_metadata.name,
            description: action.tool_metadata.description,
            args: action.tool_metadata.args,
            return_type: action.tool_metadata.return_type || undefined,
            return_description:
              action.tool_metadata.return_description || undefined,
            write_operation: action.tool_metadata.write_operation,
            role: action.tool_metadata.role,
          };
        }

        if (event.event_type === ARESimulationEventType.Env) {
          // This will put it on the UI as a notification
          notifications.push(actionMessage);
        }

        // Only add action messages if they're environment messages and environment filter is on
        // OR if they're non-environment messages and actions filter is on
        if (
          (event.event_type === ARESimulationEventType.Env &&
            infoLevel.environment) ||
          (event.event_type !== ARESimulationEventType.Env && infoLevel.actions)
        ) {
          messages.push(actionMessage);
        }
      }
    }
  }

  for (const app of appsState) {
    if (app.app_name === "WebNavigation") {
      for (const frames of Object.values(app.queries)) {
        // prettier-ignore
        // @ts-ignore
        if (frames.length === 0) {
          continue;
        }

        // prettier-ignore
        // @ts-ignore
        const timestamp = frames[0].timestamp;

        const stream: WebNavStream = {
          // prettier-ignore
          // @ts-ignore
          task: frames[0].main_question,
          frames: frames as WebNavStream["frames"],
        };

        const webNavMessage: WebNavMessageType = {
          id: timestamp.toString(),
          type: "WebNavigation",
          sender: "AGENT",
          timestamp,
          stream,
        };

        messages.push(webNavMessage);
      }
    }
  }

  // The message list is actually a tree, because subagents will nest messages. To represent that, we will use a stack to keep track of the current tree path.
  const groupStack: Array<GroupMessageType> = [
    {
      messages,
      groupId: null,
      type: "GROUP",
      depth: 0,
      groupType: "ROOT",
      timestamp: worldLogs[0]?.timestamp ?? 0,
      id: worldLogs[0]?.id ?? "",
    },
  ];

  for (const agentLog of worldLogs) {
    // Let's look for the group that should hold this log. At first we assume this does not exist
    let targetGroup: GroupMessageType | null = null;

    // We loop in reverse the group stack, but break on the root group
    while (groupStack.length > 1) {
      const group = groupStack.pop()!;

      // If the popped group matches, we make it the target group
      if (group.groupId == agentLog.groupId) {
        groupStack.push(group);
        targetGroup = group;
        break;
      }
    }

    if (targetGroup == null) {
      // This means that we have a log without a group. We are adding it to the root group as a fallback.
      if (agentLog.groupId != null) {
        const parent = worldLogs.find((log) => log.id === agentLog.groupId);

        if (parent == null) {
          console.error(
            "Error trying to create messages tree. Missing parent group for message: ",
            agentLog,
            "The parent was not found in the world logs.",
          );
        } else {
          console.error(
            "Error trying to create messages tree. Missing parent group for message: ",
            agentLog,
            "The parent was found in the world logs: ",
            parent,
          );
        }
      }

      targetGroup = groupStack[0]!;
    }

    if (agentLog.type === "STEP" || agentLog.type === "SUBAGENT") {
      const groupType: GroupType = agentLog.type;
      const group: GroupMessageType = {
        type: "GROUP",
        depth: groupStack.length,
        messages: [],
        groupId: agentLog.id,
        groupType: groupType,
        timestamp: agentLog.timestamp,
        id: agentLog.id,
      };
      targetGroup.messages.push(group);
      groupStack.push(group);
    } else if (
      agentLog.type === "THOUGHT" &&
      agentLog.content != null &&
      agentLog.timestamp != null &&
      infoLevel.thoughts
    ) {
      const thoughtMessage: ThoughtMessageType = {
        id: agentLog.id,
        type: "THOUGHT",
        sender: "AGENT",
        timestamp: agentLog.timestamp,
        content: agentLog.content,
      };

      targetGroup.messages.push(thoughtMessage);
    } else if (
      agentLog.type === "OBSERVATION" &&
      agentLog.content != null &&
      agentLog.timestamp != null
    ) {
      const observationMesage: ObservationMessageType = {
        id: agentLog.id,
        type: "OBSERVATION",
        timestamp: agentLog.timestamp,
        content: agentLog.content,
        attachments:
          agentLog.attachments?.map((attachment) => ({
            path: attachment.url,
            mime_type: attachment.mime || "",
          })) ?? [],
      };

      targetGroup.messages.push(observationMesage);
    } else if (
      agentLog.type === "FACTS" &&
      agentLog.content != null &&
      agentLog.timestamp != null &&
      infoLevel.facts
    ) {
      const factMessage: FactsMessageType = {
        id: agentLog.id,
        type: "FACTS",
        sender: "AGENT",
        timestamp: agentLog.timestamp,
        content: agentLog.content,
      };

      targetGroup.messages.push(factMessage);
    } else if (
      agentLog.type === "PLAN" &&
      agentLog.content != null &&
      agentLog.timestamp != null &&
      infoLevel.plans
    ) {
      const planMessage: PlanMessageType = {
        id: agentLog.id,
        type: "PLAN",
        sender: "AGENT",
        timestamp: agentLog.timestamp,
        content: agentLog.content,
      };

      targetGroup.messages.push(planMessage);
    } else if (agentLog.type === "LLM_INPUT") {
      if (
        infoLevel.llmOutputs &&
        (infoLevel.actions || infoLevel.thoughts) &&
        agentLog.content != null
      ) {
        const message: LLMInputOutputType = {
          id: agentLog.id,
          type: "LLMInputOutput",
          sender: "AGENT",
          timestamp: agentLog.timestamp,
          input: agentLog.content,
          output: null,
          duration: null,
        };

        targetGroup.messages.push(message);
      }
    } else if (
      agentLog.type === "LLM_OUTPUT_THOUGHT_ACTION" ||
      agentLog.type === "LLM_OUTPUT_FACTS" ||
      agentLog.type === "LLM_OUTPUT_PLAN"
    ) {
      if (
        infoLevel.llmOutputs &&
        (infoLevel.actions || infoLevel.thoughts) &&
        agentLog.content != null
      ) {
        const lastMessage =
          targetGroup.messages[targetGroup.messages.length - 1];
        if (lastMessage != null && lastMessage.type === "LLMInputOutput") {
          lastMessage.output = agentLog.content;
          lastMessage.duration = agentLog.timestamp - lastMessage.timestamp;
        } else {
          const message: LLMInputOutputType = {
            id: agentLog.id,
            type: "LLMInputOutput",
            sender: "AGENT",
            timestamp: agentLog.timestamp,
            input: "",
            output: agentLog.content,
            duration: 0,
          };

          targetGroup.messages.push(message);
        }
      }
    } else if (agentLog.type === "ERROR") {
      if (infoLevel.errors && agentLog.content) {
        const errorMessage: ErrorMessage = {
          id: agentLog.id,
          type: "ERROR",
          timestamp: agentLog.timestamp,
          content: agentLog.content,
          error: agentLog.exception ?? "",
        };

        targetGroup.messages.push(errorMessage);
      }
    }
  }

  recursiveSort(messages);

  return { messages, notifications };
}

function recursiveSort(messages: Array<Message>) {
  messages.sort((a, b) => {
    return b.timestamp - a.timestamp;
  });

  for (const message of messages) {
    if (message.type === "GROUP") {
      recursiveSort(message.messages);
    }
  }
}

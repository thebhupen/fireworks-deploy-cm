// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

export const AppViews = Object.freeze({
  SCENARIOS: "SCENARIOS",
  PLAYGROUND: "PLAYGROUND",
  DISCONNECTED: "DISCONNECTED",
});

export const AGENT_USER_INTERFACE_APP_NAME = "AgentUserInterface";

export type AppName =
  | "AgentUserInterface"
  | "ApartmentListingApp"
  | "BrowserApp"
  | "Cabs"
  | "CabApp"
  | "Calendar"
  | "CalendarApp"
  | "Chats"
  | "City"
  | "CityApp"
  | "CleverSplit"
  | "Contacts"
  | "ContactsApp"
  | "Doctor's Calendar"
  | "EmailClientApp"
  | "EmailClientV2"
  | "Emails"
  | "Facebook"
  | "Files"
  | "GenUI"
  | "Health"
  | "Instagram"
  | "Mail"
  | "Messages"
  | "MessagingApp"
  | "MessagingAppV2"
  | "Messenger"
  | "MessengerV2"
  | "Phone"
  | "RentAFlat"
  | "SandboxLocalFileSystem"
  | "SearchAgent"
  | "SearchAgentDemo"
  | "SearchInformationTool"
  | "Shopping"
  | "ShoppingApp"
  | "SocialNetwork"
  | "Spotify"
  | "SystemApp"
  | "TextInspectorTool"
  | "VirtualFileSystem"
  | "VisitTool"
  | "visualizer"
  | "WebNavigation"
  | "WhatsApp"
  | "WhatsAppV2"
  | "websearch-mcp"
  | "academia-mcp"
  | "image-edit-mcp"
  | "geocalc-mcp";

export type AppExtraData = {
  name: string;
  data: {
    app?: string;
    action?: string;
    input?: any;
    output?: any;
    exception?: string | null;
    stackTrace?: string | null;
    toolMetadata?: any;
    [key: string]: any;
  };
};

export type AppOptions = {
  extraData?: AppExtraData;
};

export const EventCreatorMode = Object.freeze({
  CREATE: "CREATE",
  EDIT: "EDIT",
  CLONE: "CLONE",
});

export type EventCreatorModeType = "CREATE" | "EDIT" | "CLONE";

export type CapabilityTag =
  | "Adaptability"
  | "Ambiguity"
  | "Execution"
  | "Search"
  | "Time";

export type ScenarioGUIConfig = {
  showTimestamps: boolean;
};

export type Scenario = {
  scenarioId: string;
  duration: number;
  startTime: number;
  timeIncrementInSeconds: number | null;
  status: string;
  comment: string;
  annotationId: string | null;
  tags: Array<CapabilityTag>;
  guiConfig: ScenarioGUIConfig;
};

export type EnvStateType =
  | "SETUP"
  | "RUNNING"
  | "STOPPED"
  | "PAUSED"
  | "FAILED";

export const EnvState = Object.freeze({
  SETUP: "SETUP",
  RUNNING: "RUNNING",
  STOPPED: "STOPPED",
  PAUSED: "PAUSED",
  FAILED: "FAILED",
});

export type ToolParam = {
  name: string;
  argType: string;
  hasDefaultValue: boolean;
  defaultValue: any;
  description: string;
  exampleValue: any;
};

export type Tool = {
  name: string;
  description: string;
  returnDescription: string;
  role: string;
  writeOperation: boolean;
  params: Array<ToolParam>;
};

export type Application = {
  appName: string;
  appTools: Array<Tool>;
};

export type ScenarioData = {
  apps: Array<Application>;
};

export type ToolInfo = {
  name: string;
  description: string;
  return_description: string;
  role: string;
  write_operation: boolean;
};

export type ParamDetails = {
  type: string;
  has_default: boolean;
  default: any;
  description: string;
  example: any;
};

export type ToolParams = {
  [key: string]: ParamDetails;
};

export type AppState = {
  app_name: AppName;
  [key: string]: any;
};

export type AppsState = ReadonlyArray<AppState>;

export type Hint = {
  associatedEventId: string;
  content: string;
  hintType: string;
};

export enum HintStatus {
  Success = "success",
  Warning = "warning",
  Error = "error",
}

export enum ARESimulationEventType {
  Agent = "AGENT",
  Env = "ENV",
  Condition = "CONDITION",
  Validation = "VALIDATION",
  User = "USER",
  Stop = "STOP",
}

export interface ARESimulationEvent {
  event_id: string;
  event_type: ARESimulationEventType;
  event_time?: number;
  event_relative_time?: number;
  event_time_comparator?: "GREATER_THAN" | "EQUAL" | "LESS_THAN" | null;
  successors: ARESimulationEvent[];
  dependencies: string[];
  action: ARESimulationEventAction;
}

export type ToolMetadataType = {
  name: string;
  description: string;
  args: Array<{
    name: string;
    type: string;
    description: string;
    has_default: boolean;
    default: any | null;
    example_value: any | null;
    arg_type: string; // Original field from Python
  }>;
  return_type: string | undefined;
  return_description: string | undefined;
  write_operation?: boolean;
  role?: string;
};

export interface ARESimulationEventAction {
  app_name: AppName;
  function_name: string;
  args: { [name: string]: any };
  resolved_args: { [name: string]: any };
  tool_metadata?: ToolMetadataType;
}

export type EventLog = Array<LogEvent>;

export type LogEvent = {
  action: ARESimulationEventAction;
  metadata: {
    return_value: string | null;
    exception?: string;
    exception_stack_trace?: string;
    completed: boolean;
  };
  event_id: string;
  event_time?: number;
  event_relative_time?: number;
  event_type: string;
};

export type AgentLogType =
  | "SYSTEM_PROMPT"
  | "TASK"
  | "LLM_INPUT"
  | "LLM_OUTPUT_THOUGHT_ACTION"
  | "RATIONALE"
  | "TOOL_CALL"
  | "OBSERVATION"
  | "STEP"
  | "FINAL_ANSWER"
  | "ERROR"
  | "THOUGHT"
  | "PLAN"
  | "FACTS"
  | "REPLAN"
  | "REFACTS"
  | "AGENT_STOP"
  | "CODE_EXECUTION_RESULT"
  | "CODE_STATE_UPDATE"
  | "END_TASK"
  | "LLM_OUTPUT_PLAN"
  | "LLM_OUTPUT_FACTS"
  | "SUBAGENT";

export type AgentLogAttachment = {
  length: number;
  mime: string;
  url: string;
};

export type AgentLog = Readonly<{
  type: AgentLogType;
  id: string;
  timestamp: number;
  groupId: string | null;
  content: string | null;
  agent_name: string | null;
  start_id: string | null;
  input: string | null;
  output: string | null;
  actionName: string | null;
  appName: string | null;
  exception: string | null;
  exceptionStackTrace: string | null;
  attachments: ReadonlyArray<AgentLogAttachment> | null;
  isSubagent: boolean | null;
}>;

export type UserPreferences = {
  annotator: {
    enhanceReadability: boolean;
  };
};

export const EDITABLE_LOG_TYPES: ReadonlyArray<AgentLogType> = [
  "SYSTEM_PROMPT",
  "LLM_OUTPUT_THOUGHT_ACTION",
  "LLM_OUTPUT_FACTS",
  "LLM_OUTPUT_PLAN",
  "OBSERVATION",
];

export function isEditableLog(
  log: AgentLog | null | undefined | void,
): boolean {
  if (!log || !log.type) {
    return false;
  }
  if (log.isSubagent === true) {
    return false;
  }
  return EDITABLE_LOG_TYPES.includes(log.type);
}

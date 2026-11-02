// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React, { useCallback, useContext, useEffect, useState } from "react";
import ResetConfirmationDialog from "../components/dialogs/ResetConfirmationDialog";
import { InfoLevel } from "../components/user-agent-dialog/InfoLevelMenu";
import { useDefaultScenarioId } from "../hooks/useDefaultScenarioId";
import useLoadScenario, {
  ScenarioSource,
  ScenarioSourceInput,
} from "../hooks/useLoadScenario";
import commitSetAgent from "../mutations/SetAgentNameMutation";
import useRelayEnvironment from "../relay/RelayEnvironment";
import appViewStorage from "../utils/AppViewStorage";
import {
  AgentLog,
  AppName,
  AppOptions,
  AppViews,
  EnvState,
  EnvStateType,
  Hint,
  ParamDetails,
  Scenario,
  ScenarioData,
  ToolInfo,
  ToolParam,
  ToolParams,
  UserPreferences,
} from "../utils/types";
import { useLocalStorage } from "../utils/useLocalStorage";
import userInfoStorage from "../utils/UserInfoStorage";
import { useAgentConfigContext } from "./AgentConfigContextProvider";
import { useNotifications } from "./NotificationsContextProvider";
import SessionIdContext from "./SessionIdContext";

export const DEFAULT_USER_PREFERENCES: UserPreferences = {
  annotator: {
    enhanceReadability: true,
  },
};

const APPS_TO_NOT_DISPLAY = ["InternalContacts"];
export const DEFAULT_AGENT = "default";
export const DEFAULT_SCENARIO = "scenario_hf_demo_mcp";

export interface AppContextType {
  // Current view of the application (Annotator, Playground)
  appView: string;
  setAppView: (appView: string) => void;
  // Current state of the environment
  envState: EnvStateType;
  setEnvState: (envState: EnvStateType) => void;
  // Local state of the environment
  localEnvState: EnvStateType;
  setLocalEnvState: (localEnvState: EnvStateType) => void;
  // Current scenario
  scenario: Scenario | null;
  setScenario: (scenario: Scenario | null) => void;
  loadScenario: (source: ScenarioSource, input: ScenarioSourceInput) => void;
  reloadScenario: () => void;
  isLoadingScenario: boolean;
  loadingScenarioId: string | undefined;
  isResettingScenario: boolean;
  setIsResettingScenario: (isResetting: boolean) => void;
  // List of available scenarios
  scenarios: Array<string>;
  setScenarios: (scenarios: Array<string>) => void;
  // Event log for the current scenario
  eventLog: Array<any>;
  setEventLog: (eventLog: Array<any>) => void;
  // Initial event queue for the current scenario
  initialEventQueue: Array<any> | null;
  setInitialEventQueue: (initialEventQueue: Array<any>) => void;
  // State of the apps in the current scenario
  appsState: Array<any>;
  setAppsState: (appsState: Array<any>) => void;
  // Map of app name to tools
  appNameToToolsMap: Map<string, Array<ToolInfo>>;
  setAppNameToToolsMap: (
    appNameToToolsMap: Map<string, Array<ToolInfo>>,
  ) => void;
  // Map of app name to tool params
  appNameToToolParamsMap: Map<string, Record<string, ToolParams>>;
  setAppNameToToolParamsMap: (
    appNameToToolParamsMap: Map<string, Record<string, ToolParams>>,
  ) => void;
  // Current user name
  userName: string | null;
  setUserName: (userName: string | null) => void;
  // Hints for the current scenario to help the agent
  hints: Array<Hint>;
  setHints: (hints: Array<Hint>) => void;
  // Currently selected app
  selectedAppName: AppName | null;
  selectedAppOptions: AppOptions | null;
  setSelectedApp: (
    selectedAppName: AppName | null,
    options?: AppOptions | null,
  ) => void;
  // Filesystem path of the session's sandbox.
  filesystemPath: string | null;
  worldLogs: ReadonlyArray<AgentLog>;
  setWorldLogs: (worldLogs: ReadonlyArray<AgentLog>) => void;
  infoLevel: InfoLevel;
  setInfoLevel: React.Dispatch<React.SetStateAction<InfoLevel>>;
  userPreferences: UserPreferences;
  setUserPreferences: (userPreferences: UserPreferences) => void;
}

/**
 * Context to provide application-wide state management.
 */
export const AppContext = React.createContext<AppContextType | null>(null);

interface AppContextProviderProps {
  children: React.ReactNode;
  value?: Partial<AppContextType>;
}

const INITIAL_INFO_LEVEL: InfoLevel = {
  errors: true,
  timestamps: false,
  environment: false,
  thoughts: true,
  actions: true,
  results: false,
  facts: true,
  plans: true,
  llmOutputs: true,
};

/**
 * AppContextProvider component that wraps its children with AppContext.Provider
 * to provide state management across the application.
 */
const AppContextProvider: React.FC<AppContextProviderProps> = ({
  children,
  value,
}) => {
  let skipResetOnAppViewChange = false;

  const { notify } = useNotifications();
  const sessionId = useContext<string>(SessionIdContext);
  const environment = useRelayEnvironment();

  // Get default scenario ID from the backend, with fallback to DEFAULT_SCENARIO
  const defaultScenarioId = useDefaultScenarioId(DEFAULT_SCENARIO);
  const [worldLogs, setWorldLogs] = useState<ReadonlyArray<AgentLog>>(
    value?.worldLogs ?? [],
  );
  const [appView, setAppViewInternal] = useState<string>(
    value?.appView ?? AppViews.DISCONNECTED,
  );
  const [showResetConfirmation, setShowResetConfirmation] = useState(false);
  const [pendingAppView, setPendingAppView] = useState<string | null>(null);
  const [envState, setEnvState] = useState<EnvStateType>(
    value?.envState ?? EnvState.SETUP,
  );
  const [localEnvState, setLocalEnvState] = useState<EnvStateType>(
    value?.localEnvState ?? EnvState.SETUP,
  );
  const [scenario, setScenarioImpl] = useState<Scenario | null>(
    value?.scenario ?? null,
  );
  const { agent, setAgent, setAgentConfig } = useAgentConfigContext();

  // Function to handle view switching with reset confirmation
  const setAppView = useCallback(
    (newView: string) => {
      if (skipResetOnAppViewChange) {
        appViewStorage.setAppView(newView);
        setAppViewInternal(newView);
        return;
      }

      // Check if we're switching between PlaygroundView and ScenariosView
      const isScenariosToPlayground =
        appView === AppViews.SCENARIOS && newView === AppViews.PLAYGROUND;

      // Check if agent or scenario are different from defaults
      const isAgentDifferent = agent !== DEFAULT_AGENT;
      const isScenarioDifferent =
        scenario?.scenarioId !== defaultScenarioId &&
        scenario?.scenarioId !== null;

      if (
        isScenariosToPlayground &&
        (isAgentDifferent || isScenarioDifferent)
      ) {
        // Show confirmation dialog only when switching between these views AND something is different
        setPendingAppView(newView);
        setShowResetConfirmation(true);
      } else {
        // Close any open apps
        setSelectedApp(null);
        // No confirmation needed, switch view directly
        appViewStorage.setAppView(newView);
        setAppViewInternal(newView);
      }
    },
    [
      appView,
      scenario?.scenarioId,
      agent,
      skipResetOnAppViewChange,
      defaultScenarioId,
    ],
  );

  const setScenario = useCallback((scenario: Scenario | null) => {
    setScenarioImpl(scenario);
    if (scenario != null) {
      setInfoLevel({
        ...INITIAL_INFO_LEVEL,
        timestamps: scenario.guiConfig.showTimestamps,
      });
    }
  }, []);
  const [scenarios, setScenarios] = useState<Array<string>>(
    value?.scenarios ?? [],
  );
  const [eventLog, setEventLog] = useState<Array<any>>(value?.eventLog ?? []);
  const [initialEventQueue, setInitialEventQueue] = useState<Array<any> | null>(
    value?.initialEventQueue ?? null,
  );
  const [appsState, setAppsState] = useState<Array<any>>(
    value?.appsState ?? [],
  );
  const [appNameToToolsMap, setAppNameToToolsMap] = useState<
    Map<string, Array<ToolInfo>>
  >(value?.appNameToToolsMap ?? new Map());
  const [appNameToToolParamsMap, setAppNameToToolParamsMap] = useState<
    Map<string, Record<string, ToolParams>>
  >(value?.appNameToToolParamsMap ?? new Map());
  const [userName, setUserName] = useState(
    value?.userName ?? userInfoStorage.getLogin(),
  );
  const [hints, setHints] = useState<Array<Hint>>(value?.hints ?? []);
  const [selectedAppName, setSelectedAppName] = useState<AppName | null>(
    value?.selectedAppName ?? null,
  );
  const [selectedAppOptions, setSelectedAppOptions] =
    useState<AppOptions | null>(value?.selectedAppOptions ?? null);
  const setSelectedApp = (
    selectedAppName: AppName | null,
    options?: AppOptions | null,
  ) => {
    setSelectedAppName(selectedAppName);
    setSelectedAppOptions(options ?? null);
  };
  const filesystemPath =
    appsState.find((app) =>
      ["Files", "SandboxLocalFileSystem"].includes(app.app_name),
    )?.tmpdir ?? null;

  const { loadScenario, reloadScenario, isLoadingScenario, loadingScenarioId } =
    useLoadScenario(
      setScenario,
      setAppNameToToolsMap,
      setAppNameToToolParamsMap,
    );
  const [isResettingScenario, setIsResettingScenario] =
    useState<boolean>(false);
  const [infoLevel, setInfoLevel] = useState<InfoLevel>(INITIAL_INFO_LEVEL);
  const [storedUserPreferences, storeUserPreferences] = useLocalStorage(
    "userPreferences",
    JSON.stringify(DEFAULT_USER_PREFERENCES),
  );
  const [userPreferences, updateUserPreferences] = useState<UserPreferences>(
    JSON.parse(storedUserPreferences),
  );
  const setUserPreferences = (userPreferences: UserPreferences) => {
    storeUserPreferences(JSON.stringify(userPreferences));
    updateUserPreferences(userPreferences);
  };

  // Sync envState with localEnvState whenever server sends updated envState
  useEffect(() => {
    setLocalEnvState(envState);
  }, [envState, setLocalEnvState]);

  // Function to handle confirmation
  const handleConfirmResetDefaults = useCallback(() => {
    // Reset agent to default
    setAgent(DEFAULT_AGENT);
    commitSetAgent(environment, DEFAULT_AGENT, sessionId, notify, (response) =>
      setAgentConfig(response),
    );
    // Reset scenario to default
    loadScenario(ScenarioSource.Code, { scenarioId: defaultScenarioId });

    // Close any open apps
    setSelectedApp(null);

    // Switch view
    if (pendingAppView) {
      appViewStorage.setAppView(pendingAppView);
      setAppViewInternal(pendingAppView);
      setPendingAppView(null);
    }

    setShowResetConfirmation(false);
  }, [
    pendingAppView,
    loadScenario,
    setAgent,
    setAgentConfig,
    environment,
    sessionId,
    notify,
    defaultScenarioId,
  ]);

  return (
    <>
      <ResetConfirmationDialog
        open={showResetConfirmation}
        onClose={() => setShowResetConfirmation(false)}
        onConfirm={handleConfirmResetDefaults}
      />
      <AppContext.Provider
        value={{
          appView,
          setAppView,
          envState,
          setEnvState,
          localEnvState,
          setLocalEnvState,
          scenario,
          setScenario,
          loadScenario,
          reloadScenario,
          isLoadingScenario,
          loadingScenarioId,
          isResettingScenario,
          setIsResettingScenario,
          scenarios,
          setScenarios,
          eventLog,
          setEventLog,
          initialEventQueue,
          setInitialEventQueue,
          appsState,
          setAppsState,
          appNameToToolsMap,
          setAppNameToToolsMap,
          appNameToToolParamsMap,
          setAppNameToToolParamsMap,
          userName,
          setUserName,
          hints,
          setHints,
          selectedAppName,
          selectedAppOptions,
          setSelectedApp,
          filesystemPath,
          worldLogs,
          setWorldLogs,
          infoLevel,
          setInfoLevel,
          userPreferences,
          setUserPreferences,
        }}
      >
        {children}
      </AppContext.Provider>
    </>
  );
};

export const processScenarioAppsData = (
  scenario: ScenarioData,
): {
  appNameToToolsMap: Map<string, Array<ToolInfo>>;
  appNameToToolParamsMap: Map<string, Record<string, ToolParams>>;
} => {
  const apps = scenario.apps ?? [];
  const appNameToToolsMap: Map<string, Array<ToolInfo>> = new Map();
  const appNameToToolParamsMap: Map<
    string,
    Record<string, ToolParams>
  > = new Map();
  apps.forEach((app) => {
    // Skip apps we should not display
    if (APPS_TO_NOT_DISPLAY.includes(app.appName)) {
      return;
    }

    const appName = app.appName;
    const toolNames = app.appTools.map((tool) => ({
      name: tool.name,
      description: tool.description,
      return_description: tool.returnDescription,
      role: tool.role,
      write_operation: tool.writeOperation,
    }));

    const toolParams = app.appTools.reduce(
      (acc: Record<string, ToolParams>, tool) => {
        acc[tool.name] = tool.params.reduce(
          (paramAcc: { [key: string]: ParamDetails }, param: ToolParam) => {
            paramAcc[param.name] = {
              type: param.argType,
              has_default: param.hasDefaultValue,
              default: param.defaultValue,
              description: param.description,
              example: param.exampleValue,
            };
            return paramAcc;
          },
          {},
        );
        return acc;
      },
      {},
    );
    appNameToToolsMap.set(appName, toolNames);
    appNameToToolParamsMap.set(appName, toolParams);
  });
  return { appNameToToolsMap, appNameToToolParamsMap };
};

export const useAppContext = () =>
  React.useContext(AppContext) as AppContextType;

export default AppContextProvider;

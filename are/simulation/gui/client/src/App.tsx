// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { RelayEnvironmentProvider, useSubscription } from "react-relay";
import "react-resizable/css/styles.css";
import { fetchQuery, graphql } from "relay-runtime";
import { EnvironmentTimeStore } from "../stores/EnvironmentTimeStore";
import "./App.css";
import LoadingSpinner from "./components/LoadingSpinner";
import LoadingStub from "./components/LoadingStub";
import AgentConfigContextProvider, {
  updateAgentConfigField,
  useAgentConfigContext,
} from "./contexts/AgentConfigContextProvider";
import AppContextProvider, {
  DEFAULT_AGENT,
  DEFAULT_SCENARIO,
  processScenarioAppsData,
  useAppContext,
} from "./contexts/AppContextProvider";
import EnvStateContext from "./contexts/EnvStateContext";
import NotificationsContextProvider, {
  useNotifications,
} from "./contexts/NotificationsContextProvider";
import { PendingMessagesProvider } from "./contexts/PendingMessagesContext";
import ScenarioContext from "./contexts/ScenarioContext";
import SessionIdContext from "./contexts/SessionIdContext";
import { useWebSocket, WebSocketProvider } from "./contexts/WebSocketProvider";
import { ScenarioSource } from "./hooks/useLoadScenario";
import commitInitConnectWithSessionId from "./mutations/InitConnectWithSessionIdMutation";
import commitSetAgentConfig from "./mutations/SetAgentConfigMutation";
import commitSetAgent from "./mutations/SetAgentNameMutation";
import commitSetUserName from "./mutations/SetUserNameMutation";
import useRelayEnvironment from "./relay/RelayEnvironment";
import appViewStorage from "./utils/AppViewStorage";
import { getSessionId } from "./utils/SessionStorage";
import { AppViews } from "./utils/types";
import userInfoStorage from "./utils/UserInfoStorage";

const Router = React.lazy(() => import("./components/Router"));

function App(): React.ReactNode {
  const sessionId = useContext<string>(SessionIdContext);
  const {
    appView,
    setAppView,
    envState,
    setEnvState,
    scenario,
    setScenario,
    isLoadingScenario,
    loadingScenarioId,
    isResettingScenario,
    loadScenario,
    setScenarios,
    setEventLog,
    setInitialEventQueue,
    setAppsState,
    setWorldLogs,
    setAppNameToToolsMap,
    setAppNameToToolParamsMap,
    setHints,
  } = useAppContext();

  const { setAgent, setAgents, setAgentConfig } = useAgentConfigContext();
  const { notify } = useNotifications();

  // prettier-ignore
  // @ts-ignore
  const { status: connectionStatus } = useWebSocket();

  const environment = useRelayEnvironment();

  const environmentStateSubscription = graphql`
    subscription AppEnvironmentSubscription($sessionId: String!) {
      environmentSubscriptionState(sessionId: $sessionId) {
        appsStateJson
        eventLogJson
        initialEventQueueJson
        envState
        environmentTime
        worldLogs {
          id
          groupId
          type
          content
          startId
          content
          timestamp
          input
          actionName
          appName
          output
          exception
          exceptionStackTrace
          attachments {
            length
            mime
            url
          }
          isSubagent
        }
        hints {
          hintType
          content
          associatedEventId
        }
      }
    }
  `;

  const StaticDataQuery = graphql`
    query AppGetStaticDataQuery {
      allScenarios
      allAgents
      defaultUiView
    }
  `;

  const SessionDataQuery = graphql`
    query AppGetSessionDataQuery($sessionId: String!) {
      activeScenario(sessionId: $sessionId) {
        guiConfig {
          showTimestamps
        }
        scenarioId
        startTime
        duration
        timeIncrementInSeconds
        status
        comment
        annotationId
        tags
        apps {
          appName
          appTools {
            name
            description
            returnDescription
            role
            writeOperation
            params {
              name
              description
              argType
              hasDefaultValue
              defaultValue
              exampleValue
            }
          }
        }
      }
      agentName(sessionId: $sessionId)
      agentConfig(sessionId: $sessionId)
    }
  `;

  const urlParams = new URLSearchParams(window.location.search);
  const urlScenario = urlParams.get("scenario");
  const urlModel = urlParams.get("model");
  const urlAgent = urlParams.get("agent");

  useEffect(() => {
    if (urlAgent != null && urlAgent !== "") {
      commitSetAgent(environment, urlAgent, sessionId, notify, (conf) => {
        if (urlModel !== undefined && urlModel !== null && urlModel !== "") {
          const updatedConfig = updateAgentConfigField(
            conf,
            "base_agent_config.llm_engine_config.model_name",
            urlModel,
          );
          if (updatedConfig !== null) {
            commitSetAgentConfig(
              environment,
              sessionId,
              notify,
              updatedConfig.value,
              (response) => {
                setAgentConfig(response.value);
              },
            );
          }
        }
      });
    }
  }, [urlAgent, urlModel]);

  useEffect(() => {
    if (
      urlScenario != null &&
      urlScenario !== "" &&
      urlScenario !== scenario?.scenarioId
    ) {
      loadScenario(ScenarioSource.Code, { scenarioId: urlScenario });
    }
  }, [urlScenario, loadScenario, scenario?.scenarioId]);

  useEffect(() => {
    if (scenario === null) {
      setAppsState([]);
    }
  }, [scenario]);

  useEffect(() => {
    if (connectionStatus === "connected") {
      fetchQuery(environment, SessionDataQuery, {
        sessionId: sessionId,
      }).subscribe({
        next: (data: any) => {
          const scenario = data?.activeScenario;
          if (scenario != null) {
            const { appNameToToolsMap, appNameToToolParamsMap } =
              processScenarioAppsData(scenario);
            setScenario({
              guiConfig: scenario.guiConfig,
              scenarioId: scenario.scenarioId,
              startTime: scenario.startTime,
              duration: scenario.duration,
              timeIncrementInSeconds: scenario.timeIncrementInSeconds,
              status: scenario.status,
              comment: scenario.comment,
              annotationId: scenario.annotationId,
              tags: scenario.tags,
            });
            setAppNameToToolsMap(appNameToToolsMap);
            setAppNameToToolParamsMap(appNameToToolParamsMap);
          }
          if (data?.agentName !== undefined) {
            if (appView === AppViews.PLAYGROUND) {
              setAgent(DEFAULT_AGENT);
            } else {
              setAgent(data?.agentName);
            }
          }
          if (data?.agentConfig !== undefined) {
            setAgentConfig(data?.agentConfig);
          }
        },

        error: (err: any) => {
          console.error(err);
          notify({
            message: "SessionDataQuery Error: " + JSON.stringify(err),
            type: "error",
          });
        },
        complete: () => {
          console.log("Session data request completed", sessionId);
        },
      });
    }
    // make sure this render when sessionId is set so we can fetch the data
    // from the server based on the sessionId
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, connectionStatus, appView]);

  const environmentStateConfig = useMemo(
    () => ({
      variables: { sessionId },
      subscription: environmentStateSubscription,
      onNext: (response: any) => {
        const environmentState = response?.environmentSubscriptionState;
        if (environmentState != null) {
          try {
            if (environmentState.appsStateJson != null) {
              const appsState = JSON.parse(
                environmentState.appsStateJson ?? "{}",
              );
              setAppsState(appsState.apps ? appsState.apps : []);
            }

            if (environmentState.worldLogs != null) {
              setWorldLogs(environmentState.worldLogs ?? []);
            }
            if (environmentState.environmentTime != null) {
              EnvironmentTimeStore.emit({
                environmentTime: environmentState.environmentTime,
              });
            }
            if (environmentState.eventLogJson != null) {
              const eventLog = JSON.parse(
                environmentState.eventLogJson ?? "{}",
              );
              setEventLog(eventLog.event_log?.past_events ?? []);
            }
            if (environmentState.initialEventQueueJson != null) {
              const initialEventQueue = JSON.parse(
                environmentState.initialEventQueueJson ?? "{}",
              );
              setInitialEventQueue(initialEventQueue ?? []);
            }
            if (environmentState.envState != null) {
              setEnvState(environmentState.envState);
            }
            if (environmentState.hints != null) {
              setHints(environmentState.hints);
            }
          } catch (error) {
            console.error("Error:", error);
            notify({
              message: "JSON parse error: " + JSON.stringify(error),
              type: "error",
            });
          }
        }
      },
      onError: (error: Error) => {
        console.error("Error in subscription:", error);
        notify({
          message:
            "EnvironmentStateSubscription Error: " + JSON.stringify(error),
          type: "error",
        });
      },
    }),
    [
      sessionId,
      environmentStateSubscription,
      isLoadingScenario,
      setAppsState,
      setEventLog,
      setInitialEventQueue,
      setEnvState,
    ],
  );

  useSubscription(environmentStateConfig);

  useEffect(() => {
    fetchQuery(environment, StaticDataQuery, {}).subscribe({
      next: (data: any) => {
        if (connectionStatus === "connected") {
          setScenarios(data?.allScenarios);
          setAgents(data?.allAgents);
          // Define which UI view mode to use by querying the server and checking local storage.
          const newView =
            appViewStorage.getAppView() ??
            data?.defaultUiView ??
            AppViews.SCENARIOS;
          if (Object.values(AppViews).includes(newView)) {
            console.log("Resolved UI view: ", newView);
            setAppView(newView);
          } else {
            console.log(
              "Invalid UI view: ",
              newView,
              " - defaulting to ",
              AppViews.PLAYGROUND,
            );
            setAgent(DEFAULT_AGENT);
            loadScenario(ScenarioSource.Code, { scenarioId: DEFAULT_SCENARIO });
            setAppView(AppViews.PLAYGROUND);
          }
        }
      },

      error: (err: any) => {
        console.error(err);
        if (connectionStatus === "connected") {
          notify({ message: "Error: " + JSON.stringify(err), type: "error" });
        } else {
          notify({
            message: "Error: lost connection to server",
            type: "error",
          });
          appView === null && setAppView(AppViews.DISCONNECTED);
        }
      },
      complete: () => {
        console.log("Static data request completed", sessionId);
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connectionStatus]);

  return (
    <>
      <LoadingSpinner
        isLoading={isLoadingScenario}
        loadingScenarioId={loadingScenarioId}
        isResetting={isResettingScenario}
      />
      <ScenarioContext.Provider
        value={{
          startTime: scenario?.startTime ?? 0,
          scenarioId: scenario?.scenarioId ?? null,
        }}
      >
        <EnvStateContext.Provider value={envState}>
          <PendingMessagesProvider>
            <Router appView={appView} />
          </PendingMessagesProvider>
        </EnvStateContext.Provider>
      </ScenarioContext.Provider>
    </>
  );
}

function AppWrapper(): React.ReactNode {
  const [sessionId, setSessionId] = useState<string>("");
  const username = userInfoStorage.getLogin();
  const isMounted: React.RefObject<boolean> = useRef(false);
  return (
    <WebSocketProvider>
      <EnvironmentInitializer
        sessionId={sessionId}
        setSessionId={setSessionId}
        username={username}
        isMounted={isMounted}
      />
    </WebSocketProvider>
  );
}

function EnvironmentInitializer({
  sessionId,
  setSessionId,
  username,
  isMounted,
}: {
  sessionId: string;
  setSessionId: (sessionId: string) => void;
  username: string | null;
  isMounted: React.RefObject<boolean>;
}) {
  const environment = useRelayEnvironment();
  useEffect(() => {
    if (!isMounted.current) {
      // prettier-ignore
      // @ts-ignore
      isMounted.current = true;
      const currentSessionId = getSessionId();
      if (currentSessionId === null) {
        throw new Error("Session ID is null");
      }
      setSessionId(currentSessionId);
      console.log("Session ID:", currentSessionId);
      // Commit the mutation only on the first render
      const notify = ({ message }: { message: string }) => {
        console.error(message);
      };
      commitInitConnectWithSessionId(environment, currentSessionId, notify);
      if (username != null) {
        commitSetUserName(environment, username, currentSessionId, notify);
      }
    }
  }, [username, environment, setSessionId, isMounted]);

  return (
    <RelayEnvironmentProvider environment={environment}>
      <React.Suspense fallback={<LoadingStub />}>
        <NotificationsContextProvider>
          <SessionIdContext.Provider value={sessionId}>
            <AgentConfigContextProvider>
              <AppContextProvider>
                {sessionId === "" ? <LoadingStub /> : <App />}
              </AppContextProvider>
            </AgentConfigContextProvider>
          </SessionIdContext.Provider>
        </NotificationsContextProvider>
      </React.Suspense>
    </RelayEnvironmentProvider>
  );
}

export default AppWrapper;

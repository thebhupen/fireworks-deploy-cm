// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Environment } from "react-relay";
import { processScenarioAppsData } from "../contexts/AppContextProvider";
import { Notify } from "../contexts/NotificationsContextProvider";
import { fetchQuery } from "../relay/RelayEnvironment";
import { CapabilityTag, Scenario, ToolInfo, ToolParams } from "../utils/types";

async function commitImportTrace(
  _environment: Environment,
  traceJson: string,
  sessionId: string,
  replayLogs: boolean,
  setScenario: (scenario: null | Scenario) => void,
  setAppsStateToToolsMap: (map: Map<string, Array<ToolInfo>>) => void,
  setAppNameToToolParamsMap: (
    map: Map<string, Record<string, ToolParams>>,
  ) => void,
  notify: Notify,
) {
  const query = `
    mutation ImportTraceMutation($traceJson: String!, $sessionId: String!, $replayLogs: Boolean!) {
      importTrace(traceJson: $traceJson, sessionId: $sessionId, replayLogs: $replayLogs) {
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
    }
  `;

  const variables = {
    traceJson,
    sessionId,
    replayLogs,
  };

  try {
    const result = await fetchQuery({ text: query }, variables);

    if (result.errors) {
      console.log("Errors:", result.errors);
      notify({
        message: "Errors: " + JSON.stringify(result.errors),
        type: "error",
      });
    } else {
      console.log("Response:", result.data);
      const scenario = result.data.importTrace;
      if (scenario != null) {
        const { appNameToToolsMap, appNameToToolParamsMap } =
          processScenarioAppsData(scenario);
        setScenario({
          guiConfig: scenario.guiConfig,
          scenarioId: scenario.scenarioId,
          startTime: scenario.startTime,
          duration: scenario.duration,
          timeIncrementInSeconds: scenario.timeIncrementInSeconds ?? null,
          status: scenario.status,
          comment: scenario.comment,
          annotationId: scenario.annotationId,
          tags: scenario.tags ? ([...scenario.tags] as CapabilityTag[]) : [],
        });
        setAppsStateToToolsMap(appNameToToolsMap);
        setAppNameToToolParamsMap(appNameToToolParamsMap);
      } else {
        notify({
          message: "Could not load scenario: " + JSON.stringify(result.data),
          type: "error",
        });
      }
    }
  } catch (err) {
    console.error(err);
    notify({
      message:
        err instanceof Error ? err.message : "Error: " + JSON.stringify(err),
      type: "error",
    });
  }
}

export default commitImportTrace;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation } from "react-relay";
import { Environment, graphql } from "relay-runtime";
import { processScenarioAppsData } from "../contexts/AppContextProvider";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";
import { err, ok, Result } from "../utils/Result";
import { CapabilityTag, Scenario, ToolInfo, ToolParams } from "../utils/types";
import type { SetScenarioMutation as SetScenarioMutationType } from "./__generated__/SetScenarioMutation.graphql";

export const SetScenarioMutation = graphql`
  mutation SetScenarioMutation($scenarioId: String!, $sessionId: String!) {
    setScenario(scenarioId: $scenarioId, sessionId: $sessionId) {
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

function commitSetScenario(
  environment: Environment,
  scenarioId: string,
  sessionId: string,
  setScenario: (scenario: Scenario | null) => void,
  setAppsStateToToolsMap: (map: Map<string, Array<ToolInfo>>) => void,
  setAppNameToToolParamsMap: (
    map: Map<string, Record<string, ToolParams>>,
  ) => void,
  notify: Notify,
): Promise<Result<void, void>> {
  const variables = {
    scenarioId,
    sessionId,
  };
  return new Promise((resolve) => {
    commitMutation<SetScenarioMutationType>(environment, {
      mutation: SetScenarioMutation,
      variables,
      onCompleted: (response, errors) => {
        resolve(ok(undefined));
        if (errors) {
          console.log("Errors:", errors);
          notify({
            message: "Errors: " + JSON.stringify(errors),
            type: "error",
          });
        } else {
          console.log("Response:", response);
          const scenario = response.setScenario;
          if (scenario != null) {
            const { appNameToToolsMap, appNameToToolParamsMap } =
              // prettier-ignore
              // @ts-ignore
              processScenarioAppsData(scenario);
            setScenario({
              guiConfig: scenario.guiConfig,
              scenarioId: scenario.scenarioId,
              startTime: scenario.startTime ?? 0,
              duration: scenario.duration ?? 0,
              timeIncrementInSeconds: scenario.timeIncrementInSeconds ?? null,
              status: scenario.status,
              comment: scenario.comment ?? "",
              annotationId: null,
              tags: scenario.tags
                ? ([...scenario.tags] as CapabilityTag[])
                : [],
            });
            setAppsStateToToolsMap(appNameToToolsMap);
            setAppNameToToolParamsMap(appNameToToolParamsMap);
          } else {
            notify({
              message: "Could not load scenario: " + JSON.stringify(response),
              type: "error",
            });
          }
        }
      },
      onError: (graphqlError: GqlError) => {
        resolve(err(undefined));
        console.error(graphqlError);
        notify({
          message:
            graphqlError?.messageFormat ??
            "Error: " + JSON.stringify(graphqlError),
          type: "error",
        });
      },
    });
  });
}

export default commitSetScenario;

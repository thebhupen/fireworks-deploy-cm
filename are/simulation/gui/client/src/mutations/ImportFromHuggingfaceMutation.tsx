// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { graphql } from "relay-runtime";
import { commitMutation } from "react-relay";
import { processScenarioAppsData } from "../contexts/AppContextProvider";
import { Notification } from "../contexts/NotificationsContextProvider";
import { CapabilityTag, Scenario, ToolInfo, ToolParams } from "../utils/types";

const mutation = graphql`
  mutation ImportFromHuggingfaceMutation(
    $datasetName: String!
    $datasetConfig: String!
    $datasetSplit: String!
    $scenarioId: String!
    $sessionId: String!
  ) {
    importFromHuggingface(
      datasetName: $datasetName
      datasetConfig: $datasetConfig
      datasetSplit: $datasetSplit
      scenarioId: $scenarioId
      sessionId: $sessionId
    ) {
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

const commitImportFromHuggingface = (
  environment: any,
  datasetName: string,
  datasetConfig: string,
  datasetSplit: string,
  scenarioId: string,
  sessionId: string,
  setScenario: (scenario: Scenario | null) => void,
  setAppNameToToolsMap: (
    appNameToToolsMap: Map<string, Array<ToolInfo>>,
  ) => void,
  setAppNameToToolParamsMap: (
    appNameToToolParamsMap: Map<string, Record<string, ToolParams>>,
  ) => void,
  notify: (notification: Notification) => void,
) => {
  return new Promise((resolve, reject) => {
    commitMutation(environment, {
      mutation,
      variables: {
        datasetName,
        datasetConfig,
        datasetSplit,
        scenarioId,
        sessionId,
      },
      onCompleted: (response: any, errors: any) => {
        if (errors) {
          console.error(errors);
          notify({
            message:
              "Error importing scenario from Huggingface: " + errors[0].message,
            type: "error",
          });
          reject(errors);
          return;
        }

        const scenario = response.importFromHuggingface;
        if (!scenario) {
          notify({
            message: "Failed to import scenario from Huggingface",
            type: "error",
          });
          reject(new Error("Failed to import scenario from Huggingface"));
          return;
        }

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
        setAppNameToToolsMap(appNameToToolsMap);
        setAppNameToToolParamsMap(appNameToToolParamsMap);

        notify({
          message: "Successfully imported scenario from Huggingface",
          type: "success",
        });

        resolve(scenario);
      },
      onError: (error: Error) => {
        console.error(error);
        notify({
          message:
            "Error importing scenario from Huggingface: " + error.message,
          type: "error",
        });
        reject(error);
      },
    });
  });
};

export default commitImportFromHuggingface;

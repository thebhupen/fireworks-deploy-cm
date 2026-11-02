// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useContext, useState } from "react";
import { useMutation } from "react-relay";
import { useNotifications } from "../contexts/NotificationsContextProvider";
import SessionIdContext from "../contexts/SessionIdContext";
import commitImportFromHuggingface from "../mutations/ImportFromHuggingfaceMutation";
import commitImportFromLocalJsonDataset from "../mutations/ImportFromLocalJsonDatasetMutation";
import commitImportTrace from "../mutations/ImportTraceMutation";
import commitSetScenario from "../mutations/SetScenarioMutation";
import { StopMutation } from "../mutations/StopMutation";
import useRelayEnvironment from "../relay/RelayEnvironment";
import { readFileAsText } from "../utils/fileUtils";
import { Scenario, ToolInfo, ToolParams } from "../utils/types";

export enum ScenarioSource {
  Code = "Code",
  File = "File",
  Url = "Url",
  Database = "Database",
  Huggingface = "Huggingface",
  LocalJsonDataset = "LocalJsonDataset",
}

export interface HuggingfaceDatasetInfo {
  datasetName: string;
  datasetConfig: string;
  datasetSplit: string;
  scenarioId: string;
}

export interface LocalJsonDatasetInfo {
  capability: string;
  datasetFilename: string;
}

export interface ScenarioSourceInput {
  scenarioId?: string;
  file?: File;
  url?: string;
  huggingfaceInfo?: HuggingfaceDatasetInfo;
  localJsonDatasetInfo?: LocalJsonDatasetInfo;
  replayLogs?: boolean;
}

export interface LoadScenarioOptions {
  replayLogs: boolean;
}

const SCENARIO_SOURCE_KEY = "scenario_source";
const SCENARIO_INPUT_KEY = "scenario_input";

const loadSourceFromLocalStorage = () => {
  const source = localStorage.getItem(SCENARIO_SOURCE_KEY);
  if (source) {
    return source as ScenarioSource;
  }
  return null;
};

const loadInputFromLocalStorage = () => {
  const input = localStorage.getItem(SCENARIO_INPUT_KEY);
  if (input) {
    return JSON.parse(input);
  }
  return null;
};

/**
 * Custom hook to load a scenario using a given scenario ID.
 * It manages the state and side effects related to loading a scenario.
 *
 * @returns {Object} - An object containing the loadScenario function and a boolean indicating if the scenario is loading.
 */
const useLoadScenario = (
  setScenario: (scenario: Scenario | null) => void,
  setAppNameToToolsMap: (
    appNameToToolsMap: Map<string, Array<ToolInfo>>,
  ) => void,
  setAppNameToToolParamsMap: (
    appNameToToolParamsMap: Map<string, Record<string, ToolParams>>,
  ) => void,
) => {
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const [commitStop] = useMutation(StopMutation);
  const { notify } = useNotifications();
  const [isLoadingScenario, setIsLoadingScenario] = useState(false);
  const [loadingScenarioId, setLoadingScenarioId] = useState<
    string | undefined
  >(undefined);
  const [source, setSource] = useState<ScenarioSource | null>(
    loadSourceFromLocalStorage(),
  );
  const [input, setInput] = useState<ScenarioSourceInput | null>(
    loadInputFromLocalStorage(),
  );

  const updateSource = (source: ScenarioSource) => {
    setSource(source);
    localStorage.setItem(SCENARIO_SOURCE_KEY, source as string);
  };

  const updateInput = (input: ScenarioSourceInput) => {
    setInput(input);
    localStorage.setItem(SCENARIO_INPUT_KEY, JSON.stringify(input));
  };

  const loadScenarioFromCode = async (scenarioId?: string) => {
    if (!scenarioId) {
      throw new Error("Scenario ID is required");
    }
    await commitSetScenario(
      environment,
      scenarioId,
      sessionId,
      setScenario,
      setAppNameToToolsMap,
      setAppNameToToolParamsMap,
      notify,
    );
  };

  const loadScenarioFromFile = async (
    file?: File,
    replayLogs: boolean = false,
  ) => {
    if (!file) {
      notify({
        message: "File is required",
        type: "error",
      });
      return;
    }
    const fileContent = await readFileAsText(file);
    await commitImportTrace(
      environment,
      fileContent,
      sessionId,
      replayLogs,
      setScenario,
      setAppNameToToolsMap,
      setAppNameToToolParamsMap,
      notify,
    );
  };

  const loadScenarioFromUrl = async (
    url?: string,
    replayLogs: boolean = false,
  ) => {
    if (!url) {
      throw new Error("URL is required");
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch data from URL: ${response.statusText}`);
    }
    const data = await response.json();
    await commitImportTrace(
      environment,
      JSON.stringify(data),
      sessionId,
      replayLogs,
      setScenario,
      setAppNameToToolsMap,
      setAppNameToToolParamsMap,
      notify,
    );
  };

  /**
   * Loads a scenario from Huggingface, commits the mutation, and updates the context state.
   *
   * @param {string} _scenarioId - Unused parameter (kept for consistency with other load functions)
   * @param {HuggingfaceDatasetInfo} huggingfaceInfo - Information about the Huggingface dataset and scenario
   */
  const loadScenarioFromHuggingface = async (
    _scenarioId?: string,
    huggingfaceInfo?: HuggingfaceDatasetInfo,
  ) => {
    if (!huggingfaceInfo) {
      throw new Error("Huggingface dataset information is required");
    }

    try {
      const { datasetName, datasetConfig, datasetSplit, scenarioId } =
        huggingfaceInfo;

      await commitImportFromHuggingface(
        environment,
        datasetName,
        datasetConfig,
        datasetSplit,
        scenarioId,
        sessionId,
        setScenario,
        setAppNameToToolsMap,
        setAppNameToToolParamsMap,
        notify,
      );
    } catch (error) {
      console.error("Error loading scenario from Huggingface:", error);
      throw new Error(
        `Failed to load scenario from Huggingface: ${(error as Error).message}`,
      );
    }
  };

  /**
   * Loads a scenario from a local JSON dataset file.
   *
   * @param {LocalJsonDatasetInfo} localJsonDatasetInfo - Information about the local JSON dataset
   * @param {boolean} replayLogs - Whether to replay the logs after importing
   */
  const loadScenarioFromLocalJsonDataset = async (
    localJsonDatasetInfo?: LocalJsonDatasetInfo,
    replayLogs: boolean = false,
  ) => {
    if (!localJsonDatasetInfo) {
      throw new Error("Local JSON dataset information is required");
    }

    const { capability, datasetFilename } = localJsonDatasetInfo;

    try {
      await commitImportFromLocalJsonDataset(
        environment,
        capability,
        datasetFilename,
        sessionId,
        replayLogs,
        setScenario,
        setAppNameToToolsMap,
        setAppNameToToolParamsMap,
        notify,
      );
    } catch (error) {
      console.error("Error loading scenario from local JSON dataset:", error);
      throw new Error(
        `Failed to load scenario from local JSON dataset: ${(error as Error).message}`,
      );
    }
  };

  const handleLoadScenarioFromSource = async (
    source: ScenarioSource,
    input: ScenarioSourceInput,
  ) => {
    try {
      switch (source) {
        case ScenarioSource.Code:
          await loadScenarioFromCode(input.scenarioId);
          break;
        case ScenarioSource.File:
          await loadScenarioFromFile(input.file, input.replayLogs || false);
          break;
        case ScenarioSource.Url:
          await loadScenarioFromUrl(input.url, input.replayLogs || false);
          break;
        case ScenarioSource.Huggingface:
          await loadScenarioFromHuggingface(
            input.scenarioId,
            input.huggingfaceInfo,
          );
          break;
        case ScenarioSource.LocalJsonDataset:
          await loadScenarioFromLocalJsonDataset(
            input.localJsonDatasetInfo,
            input.replayLogs || false,
          );
          break;
      }
      updateSource(source);
      updateInput(input);
    } catch (error) {
      console.error(error);
      notify({
        message: "Could not load scenario: " + (error as Error).message,
        type: "error",
      });
    }
    setIsLoadingScenario(false);
    setLoadingScenarioId(undefined);
  };

  const loadScenario = async (
    source: ScenarioSource,
    input: ScenarioSourceInput,
  ) => {
    setIsLoadingScenario(true);
    setLoadingScenarioId(input.scenarioId);
    commitStop({
      variables: {
        sessionId,
      },
      onCompleted: () => {
        handleLoadScenarioFromSource(source, input);
      },
      onError: (error) => {
        setIsLoadingScenario(false);
        setLoadingScenarioId(undefined);
        console.error(`Error stopping scenario: ${error.message}`);
        notify({
          type: "error",
          message: "Error stopping scenario",
        });
      },
    });
  };

  const reloadScenario = () => {
    if (source && input) {
      loadScenario(source, input);
    } else {
      notify({
        message: "No scenario to reload",
        type: "error",
      });
    }
  };

  return {
    loadScenario,
    reloadScenario,
    isLoadingScenario,
    loadingScenarioId,
  };
};

export default useLoadScenario;

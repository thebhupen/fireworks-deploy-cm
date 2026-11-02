// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Stack } from "@mui/material";
import { ReactFlowProvider } from "@xyflow/react";
import EventDag from "../../components/dag/EventDag";
import PageLayout from "../../components/layout/PageLayout";
import ScenariosHeader from "../../components/scenarios/ScenariosHeader";
import { useAppContext } from "../../contexts/AppContextProvider";
import AvailableAppsContext from "../../contexts/AvailableAppsContext";
import { ScenarioDebugProvider } from "../../contexts/ScenarioDebugContext";
import ScenarioExecutionContext from "../../contexts/ScenarioExecutionContext";
import { EnvState } from "../../utils/types";

const ScenariosView = () => {
  const {
    appNameToToolsMap,
    appNameToToolParamsMap,
    envState,
    initialEventQueue,
  } = useAppContext();
  const isUndefined = envState === undefined;
  const isRunning = !isUndefined && envState === EnvState.RUNNING;
  const isEditable =
    !isUndefined &&
    (envState === EnvState.STOPPED || envState === EnvState.SETUP);
  let content = (
    <>
      <ScenariosHeader />
      <EventDag events={initialEventQueue} />
    </>
  );

  return (
    <PageLayout>
      <ScenarioExecutionContext.Provider value={{ isRunning, isEditable }}>
        <AvailableAppsContext.Provider
          value={{ appNameToToolsMap, appNameToToolParamsMap }}
        >
          <ScenarioDebugProvider>
            <ReactFlowProvider>
              <Stack width={"100%"}>{content}</Stack>
            </ReactFlowProvider>
          </ScenarioDebugProvider>
        </AvailableAppsContext.Provider>
      </ScenarioExecutionContext.Provider>
    </PageLayout>
  );
};

export default ScenariosView;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { createContext } from "react";

type ScenarioContextType = {
  startTime: number;
  scenarioId: null | string;
};

const ScenarioContext: React.Context<ScenarioContextType> =
  createContext<ScenarioContextType>({
    startTime: 0,
    scenarioId: null,
  });

export default ScenarioContext;

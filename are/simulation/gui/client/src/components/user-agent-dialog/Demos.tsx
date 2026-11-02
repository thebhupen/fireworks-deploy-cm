// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { DEFAULT_SCENARIO } from "../../contexts/AppContextProvider";

export type DialogTree = { [option: string]: DialogTree };
// This represents a dialog tree like:
// {
//   "option A": {
//     "option A.1": {},
//     "option A.2": {},
//   },
//   "option B": {
//     "option B.1": {}
//   },
// }

export function calculateNextDialogTree(
  dialogTree: DialogTree,
  selections: Array<string>,
): DialogTree | null {
  let current = dialogTree;

  for (const selection of selections) {
    current = current[selection];

    if (current == null) {
      return null;
    }
  }

  return current;
}

export type ScenarioSelection = {
  id: string;
  label: string;
  defaultQuestions: DialogTree;
};

export const INTERACTIVE_SCENARIOS: Record<string, ScenarioSelection> = {
  [DEFAULT_SCENARIO]: {
    id: DEFAULT_SCENARIO,
    label: "default",
    defaultQuestions: {
      "Briefly summarize the last 3 emails I have received": {},
      "Send a birthday party invitation to all of my contacts living in Menlo Park":
        {},
      "Help me prep for my AI work meetings this week": {},
    },
  },
};

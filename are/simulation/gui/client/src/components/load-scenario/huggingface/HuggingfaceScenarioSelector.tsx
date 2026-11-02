// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useLazyLoadQuery } from "react-relay";
import { graphql } from "relay-runtime";
import { FormControl, TextField, Autocomplete } from "@mui/material";
import FormInputLabel from "../../common/inputs/FormInputLabel";
import type { HuggingfaceScenarioSelectorQuery } from "./__generated__/HuggingfaceScenarioSelectorQuery.graphql";

// GraphQL query for fetching scenarios
export const getHuggingfaceScenariosQuery = graphql`
  query HuggingfaceScenarioSelectorQuery(
    $datasetName: String!
    $datasetConfig: String!
    $datasetSplit: String!
  ) {
    getHuggingfaceScenarios(
      datasetName: $datasetName
      datasetConfig: $datasetConfig
      datasetSplit: $datasetSplit
    ) @required(action: THROW)
  }
`;

// Component that fetches and displays scenarios
export function HuggingfaceScenarioSelector({
  datasetName,
  datasetConfig,
  datasetSplit,
  scenarioId,
  onScenarioSelect,
}: {
  datasetName: string;
  datasetConfig: string;
  datasetSplit: string;
  scenarioId: string | null;
  onScenarioSelect: (scenarioId: string | null) => void;
}) {
  const data = useLazyLoadQuery<HuggingfaceScenarioSelectorQuery>(
    getHuggingfaceScenariosQuery,
    {
      datasetName,
      datasetConfig,
      datasetSplit,
    },
  );

  // Extract scenarios from the query result
  const scenarios = data?.getHuggingfaceScenarios || [];

  return (
    <FormControl>
      <FormInputLabel label="Select a scenario" />
      <Autocomplete
        options={scenarios}
        renderInput={(params) => (
          <TextField {...params} placeholder="Select a scenario" />
        )}
        value={scenarioId}
        onChange={(_, value) => onScenarioSelect(value)}
        size="small"
      />
    </FormControl>
  );
}

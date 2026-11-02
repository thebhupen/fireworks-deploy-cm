// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useState } from "react";
import { useLazyLoadQuery } from "react-relay";
import { graphql } from "relay-runtime";
import { FormControl, TextField, Autocomplete } from "@mui/material";
import FormInputLabel from "../../common/inputs/FormInputLabel";
import type { HuggingfaceDatasetSplitSelectorQuery } from "./__generated__/HuggingfaceDatasetSplitSelectorQuery.graphql";

// GraphQL query for fetching dataset configs
export const getHuggingfaceDatasetSplitsQuery = graphql`
  query HuggingfaceDatasetSplitSelectorQuery(
    $datasetName: String!
    $datasetConfig: String!
  ) {
    getHuggingfaceDatasetSplits(
      datasetName: $datasetName
      datasetConfig: $datasetConfig
    ) @required(action: THROW)
  }
`;

// Component that fetches and displays dataset configs
export function HuggingfaceDatasetSplitSelector({
  datasetName,
  datasetConfig,
  onSplitSelect,
}: {
  datasetName: string;
  datasetConfig: string;
  onSplitSelect: (config: string | null) => void;
}) {
  const [selectedSplit, setSelectedSplit] = useState<string | null>(null);

  const data = useLazyLoadQuery<HuggingfaceDatasetSplitSelectorQuery>(
    getHuggingfaceDatasetSplitsQuery,
    {
      datasetName,
      datasetConfig,
    },
  );

  // Extract splits from the query result
  const splits = data?.getHuggingfaceDatasetSplits || [];

  // Handle split selection
  const handleSplitChange = (value: string | null) => {
    setSelectedSplit(value);
    onSplitSelect(value);
  };

  return (
    <FormControl>
      <FormInputLabel label="Select a split" />
      <Autocomplete
        options={splits}
        renderInput={(params) => (
          <TextField {...params} placeholder="Select a split" />
        )}
        value={selectedSplit}
        onChange={(_, value) => handleSplitChange(value)}
        size="small"
      />
    </FormControl>
  );
}

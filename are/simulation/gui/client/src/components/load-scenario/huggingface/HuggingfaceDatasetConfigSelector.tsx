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
import type { HuggingfaceDatasetConfigSelectorQuery } from "./__generated__/HuggingfaceDatasetConfigSelectorQuery.graphql";

// GraphQL query for fetching dataset configs
export const getHuggingfaceDatasetConfigsQuery = graphql`
  query HuggingfaceDatasetConfigSelectorQuery($datasetName: String!) {
    getHuggingfaceDatasetConfigs(datasetName: $datasetName)
      @required(action: THROW)
  }
`;

// Component that fetches and displays dataset configs
export function HuggingfaceDatasetConfigSelector({
  datasetName,
  onConfigSelect,
}: {
  datasetName: string;
  onConfigSelect: (config: string | null) => void;
}) {
  const [selectedConfig, setSelectedConfig] = useState<string | null>(null);

  const data = useLazyLoadQuery<HuggingfaceDatasetConfigSelectorQuery>(
    getHuggingfaceDatasetConfigsQuery,
    {
      datasetName,
    },
  );

  // Extract configs from the query result
  const configs = data?.getHuggingfaceDatasetConfigs || [];

  // Handle config selection
  const handleConfigChange = (value: string | null) => {
    setSelectedConfig(value);
    onConfigSelect(value);
  };

  return (
    <FormControl>
      <FormInputLabel label="Select a capability" />
      <Autocomplete
        options={configs}
        renderInput={(params) => (
          <TextField {...params} placeholder="Select a capability" />
        )}
        value={selectedConfig}
        onChange={(_, value) => handleConfigChange(value)}
        size="small"
      />
    </FormControl>
  );
}

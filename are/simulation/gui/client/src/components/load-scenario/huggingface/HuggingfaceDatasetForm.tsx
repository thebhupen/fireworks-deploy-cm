// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Box,
  Button,
  FormControl,
  FormControlLabel,
  LinearProgress,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Suspense, useState } from "react";
import {
  GAIA_V2_DATASET_NAME,
  GAIA_V2_DATASET_DISPLAY_NAME,
} from "../../../constants/agentConstants";
import { HuggingfaceDatasetInfo } from "../../../hooks/useLoadScenario";
import { ErrorBoundary } from "../../common/ErrorBoundary";
import FormInputLabel from "../../common/inputs/FormInputLabel";
import { HuggingfaceDatasetConfigSelector } from "./HuggingfaceDatasetConfigSelector";
import { HuggingfaceDatasetSplitSelector } from "./HuggingfaceDatasetSplitSelector";
import { HuggingfaceScenarioSelector } from "./HuggingfaceScenarioSelector";

function Progress({ label }: { label: string }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
      <Box sx={{ flexGrow: 1 }}>
        <LinearProgress />
      </Box>
      <Typography variant="body2" color="text.secondary">
        {label}...
      </Typography>
    </Box>
  );
}

export function HuggingfaceForm({
  initialDatasetName = GAIA_V2_DATASET_NAME,
  initialDatasetConfig = "",
  initialDatasetSplit = "",
  onSelectScenario,
}: {
  initialDatasetName?: string;
  initialDatasetConfig?: string;
  initialDatasetSplit?: string;
  onSelectScenario: (info: HuggingfaceDatasetInfo | null) => void;
}) {
  const [datasetName, setDatasetName] = useState<string>(initialDatasetName);
  const [datasetConfig, setDatasetConfig] = useState<string | null>(
    initialDatasetConfig || null,
  );
  const [datasetSplit, setDatasetSplit] = useState<string | null>(
    initialDatasetSplit || null,
  );

  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(
    null,
  );
  const [datasetOption, setDatasetOption] = useState<"gaiav2" | "other">(
    initialDatasetName === GAIA_V2_DATASET_NAME ? "gaiav2" : "other",
  );

  // Handle config selection
  const handleConfigSelect = (config: string | null) => {
    setDatasetConfig(config);

    if (!config) {
      onSelectScenario(null);
    }
  };

  // Handle split selection
  const handleSplitSelect = (split: string | null) => {
    setDatasetSplit(split);

    if (!split) {
      onSelectScenario(null);
    }
  };

  // Handle scenario selection
  const handleScenarioSelect = (selectedScenarioId: string | null) => {
    setSelectedScenarioId(selectedScenarioId);
    if (selectedScenarioId && datasetName && datasetConfig && datasetSplit) {
      onSelectScenario({
        datasetName,
        datasetConfig,
        datasetSplit,
        scenarioId: selectedScenarioId,
      });
    } else {
      onSelectScenario(null);
    }
  };

  const [loadDataset, setLoadDataset] = useState<boolean>(
    initialDatasetName !== "",
  );

  // Handle dataset option change
  const handleDatasetOptionChange = (option: "gaiav2" | "other") => {
    setDatasetOption(option);
    if (option === "gaiav2") {
      setDatasetName(GAIA_V2_DATASET_NAME);
      setLoadDataset(true);
    } else {
      setDatasetName("");
      setLoadDataset(false);
    }
    setDatasetConfig(null);
    setDatasetSplit(null);
    onSelectScenario(null);
  };

  // Reset the form when dataset name changes
  const handleDatasetNameChange = (newDatasetName: string) => {
    setDatasetName(newDatasetName);
    setDatasetConfig(null);
    setDatasetSplit(null);
    setLoadDataset(false);
    onSelectScenario(null);
  };

  // Handle load dataset button click
  const handleLoadDataset = () => {
    setLoadDataset(true);
  };

  return (
    <Stack spacing={2}>
      <FormControl>
        <FormInputLabel label="Hugging Face Dataset" />
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <RadioGroup
            value={datasetOption}
            onChange={(e) =>
              handleDatasetOptionChange(e.target.value as "gaiav2" | "other")
            }
            row
          >
            <FormControlLabel
              value="gaiav2"
              control={<Radio />}
              label={GAIA_V2_DATASET_DISPLAY_NAME}
            />
            <FormControlLabel value="other" control={<Radio />} label="Other" />
          </RadioGroup>

          {datasetOption === "other" && (
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                width: "270px",
              }}
            >
              <TextField
                value={datasetName}
                onChange={(e) => handleDatasetNameChange(e.target.value)}
                size="small"
                placeholder="organization/dataset"
                fullWidth
              />
              <Button
                variant="contained"
                size="small"
                onClick={handleLoadDataset}
                disabled={!datasetName || loadDataset}
              >
                Load
              </Button>
            </Box>
          )}
        </Box>
      </FormControl>

      <ErrorBoundary fallback={<div>Failed to load dataset.</div>}>
        {datasetName && loadDataset && (
          <Suspense fallback={<Progress label="Loading configs" />}>
            <HuggingfaceDatasetConfigSelector
              datasetName={datasetName}
              onConfigSelect={handleConfigSelect}
            />
          </Suspense>
        )}

        {datasetName && datasetConfig && (
          <Suspense fallback={<Progress label="Loading splits" />}>
            <HuggingfaceDatasetSplitSelector
              datasetName={datasetName}
              datasetConfig={datasetConfig}
              onSplitSelect={handleSplitSelect}
            />
          </Suspense>
        )}

        {datasetName && datasetConfig && datasetSplit && (
          <Suspense fallback={<Progress label="Loading scenarios" />}>
            <HuggingfaceScenarioSelector
              scenarioId={selectedScenarioId}
              datasetName={datasetName}
              datasetConfig={datasetConfig}
              datasetSplit={datasetSplit}
              onScenarioSelect={handleScenarioSelect}
            />
          </Suspense>
        )}
      </ErrorBoundary>
    </Stack>
  );
}

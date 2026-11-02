// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CodeIcon from "@mui/icons-material/Code";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import LinkIcon from "@mui/icons-material/Link";
import {
  Autocomplete,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  MenuItem,
  Select,
  Stack,
  TextField,
} from "@mui/material";
import { JSX, useEffect, useMemo, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import {
  ScenarioSource,
  ScenarioSourceInput,
} from "../../hooks/useLoadScenario";
import FileInput from "../common/inputs/FileInput";
import FormInputLabel from "../common/inputs/FormInputLabel";
import HuggingFaceIcon from "../icons/HuggingFaceLogo";
import ImportOptions from "./ImportOptions";
import { HuggingfaceForm } from "./huggingface/HuggingfaceDatasetForm";

interface LoadScenarioDialogProps {
  isOpen: boolean;
  onClose: () => void;
  defaultSource?: ScenarioSource;
}

const LoadScenarioDialog = ({
  isOpen,
  onClose,
  defaultSource = ScenarioSource.Code,
}: LoadScenarioDialogProps) => {
  const { loadScenario, scenarios } = useAppContext();
  const [source, setSource] = useState<ScenarioSource>(defaultSource);
  const [input, setInput] = useState<ScenarioSourceInput | null>(null);
  const [replayLogs, setReplayLogs] = useState<boolean>(false);

  // Reset on open
  useEffect(() => {
    if (isOpen) {
      setInput(null);
      setSource(defaultSource);
      setReplayLogs(false);
    }
  }, [isOpen, defaultSource]);

  const handleLoadScenario = () => {
    if (input == null) {
      return;
    }
    const inputWithReplayLogs = { ...input, replayLogs };
    loadScenario(source, inputWithReplayLogs);
    onClose();
  };

  const extraSourceOptions: JSX.Element[] = [];

  const getLoadScenarioInput = (source: ScenarioSource) => {
    switch (source) {
      case ScenarioSource.Huggingface:
        return (
          <HuggingfaceForm
            onSelectScenario={(huggingfaceInput) => {
              setInput(
                huggingfaceInput
                  ? {
                      huggingfaceInfo: huggingfaceInput,
                    }
                  : null,
              );
            }}
          />
        );
      case ScenarioSource.Code:
        return (
          <FormControl>
            <FormInputLabel label="Scenario" />
            <Autocomplete
              options={scenarios}
              renderInput={(params) => (
                <TextField {...params} placeholder="Select scenario" />
              )}
              value={input?.scenarioId ?? null}
              onChange={(_, value) => {
                setInput({ scenarioId: value! });
              }}
              size="small"
            />
          </FormControl>
        );
      case ScenarioSource.File:
        return (
          <FileInput
            onFileSelected={(file) => {
              setInput(file ? { file } : null);
            }}
            selectedFile={input?.file ?? null}
          />
        );
      case ScenarioSource.Url:
        return (
          <FormControl>
            <FormInputLabel label="External file URL" />
            <TextField
              value={input?.url ?? ""}
              onChange={(e) => {
                setInput({ url: e.target.value });
              }}
              size="small"
              placeholder="https://example.com/example.json"
            />
          </FormControl>
        );
    }
  };

  const isDisabled = useMemo(() => {
    if (input == null) {
      return true;
    }
    switch (source) {
      case ScenarioSource.Code:
        return !input.scenarioId;
      case ScenarioSource.File:
        return !input.file;
      case ScenarioSource.Url:
        return !input.url;
      case ScenarioSource.Huggingface:
        return !input.huggingfaceInfo;
      case ScenarioSource.LocalJsonDataset:
        return (
          !input.localJsonDatasetInfo?.capability ||
          !input.localJsonDatasetInfo?.datasetFilename
        );
      case ScenarioSource.Database:
        return !input.scenarioId;
    }
  }, [input, source]);

  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="md">
      <DialogTitle>Load scenario</DialogTitle>
      <DialogContent sx={{ minWidth: "500px", minHeight: "220px" }}>
        <Stack spacing={2}>
          <FormControl>
            <FormInputLabel label="Source" />
            <Select
              value={source}
              onChange={(e) => {
                setSource(e.target.value as ScenarioSource);
                setInput(null);
              }}
              size="small"
            >
              <MenuItem value={ScenarioSource.Huggingface}>
                <Stack direction={"row"} alignItems={"center"} spacing={2}>
                  <span
                    style={{
                      width: "21px",
                      height: "21px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "18px",
                    }}
                  >
                    <HuggingFaceIcon />
                  </span>{" "}
                  <span>Hugging Face</span>
                </Stack>
              </MenuItem>
              <MenuItem value={ScenarioSource.Code}>
                <Stack direction={"row"} alignItems={"center"} spacing={2}>
                  <CodeIcon /> <span>Code</span>
                </Stack>
              </MenuItem>
              <MenuItem value={ScenarioSource.File}>
                <Stack direction={"row"} alignItems={"center"} spacing={2}>
                  <InsertDriveFileOutlinedIcon /> <span>File</span>
                </Stack>
              </MenuItem>
              <MenuItem value={ScenarioSource.Url}>
                <Stack direction={"row"} alignItems={"center"} spacing={2}>
                  <LinkIcon /> <span>URL</span>
                </Stack>
              </MenuItem>
              {extraSourceOptions.map((option) => option)}
            </Select>
          </FormControl>
          {getLoadScenarioInput(source)}
          {(source === ScenarioSource.File ||
            source === ScenarioSource.Url ||
            source === ScenarioSource.LocalJsonDataset) && (
            <ImportOptions
              replayLogs={replayLogs}
              onReplayLogsChange={setReplayLogs}
            />
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={() => {
            onClose();
          }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleLoadScenario}
          disabled={isDisabled}
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LoadScenarioDialog;

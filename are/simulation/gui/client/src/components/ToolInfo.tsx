// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Typography,
  Box,
  Paper,
  Chip,
  Divider,
  Button,
  Alert,
} from "@mui/material";
import * as React from "react";
import { useState, useCallback, useContext } from "react";
import JSONView from "./JSONView";
import { stripAppNamePrefix } from "../utils/toolUtils";

import ToolParamsForm from "./ToolParamsForm";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useNotifications } from "../contexts/NotificationsContextProvider";
import { useRelayEnvironment } from "react-relay";
import commitExecuteAppTool from "../mutations/ExecuteAppToolMutation";
import SessionIdContext from "../contexts/SessionIdContext";
import { ToolMetadataType } from "../utils/types";

interface ToolInfoProps {
  selectedTool: ToolMetadataType;
  appName: string;
  isRunnable?: boolean;
  toolParams: Record<string, any>;
}

/**
 * ToolInfo component displays detailed information about a tool.
 * It shows the tool's name, description, parameters, and execution controls.
 *
 * @param props - Component props
 * @returns React component displaying tool information
 */
function ToolInfo(props: ToolInfoProps): React.ReactNode {
  const { selectedTool, appName, isRunnable = false, toolParams } = props;
  const [paramValues, setParamValues] = useState<Record<string, any>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [toolReturnValue, setToolReturnValue] = useState<any>(null);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();
  const sessionId = useContext<string>(SessionIdContext);

  const handleParamChange = useCallback((paramName: string, value: any) => {
    setParamValues((prev) => ({
      ...prev,
      [paramName]: value,
    }));
  }, []);

  const handleExecuteTool = useCallback(() => {
    if (!selectedTool) return;

    setIsExecuting(true);

    if (!sessionId) {
      notify({
        message: "Session ID not found. Please refresh the page.",
        type: "error",
      });
      setIsExecuting(false);
      return;
    }

    // Reset the return value when executing a new tool
    setToolReturnValue(null);

    commitExecuteAppTool(
      environment,
      sessionId,
      appName,
      stripAppNamePrefix(selectedTool.name, appName),
      paramValues,
      notify,
      (response) => {
        setIsExecuting(false);
        // Handle the return value from the tool execution
        if (response?.executeAppTool?.returnValue) {
          try {
            // Try to parse the JSON string
            const parsedValue = JSON.parse(response.executeAppTool.returnValue);
            setToolReturnValue(parsedValue);
          } catch (error) {
            // If parsing fails, use the raw string
            setToolReturnValue(response.executeAppTool.returnValue);
          }
        }
      },
      (errors) => {
        setIsExecuting(false);
        console.error("Error executing tool:", errors);
      },
    );
  }, [
    selectedTool,
    sessionId,
    appName,
    paramValues,
    notify,
    environment,
    stripAppNamePrefix,
  ]);

  return (
    <Paper elevation={2} sx={{ p: 2, mt: 2 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h5" color="primary" gutterBottom>
          {stripAppNamePrefix(selectedTool.name, appName)}
        </Typography>

        <Chip
          label={
            selectedTool.write_operation === true
              ? "Write Operation"
              : "Read Operation"
          }
          color={selectedTool.write_operation === true ? "warning" : "info"}
          size="small"
          sx={{ mb: 2 }}
        />

        <Typography variant="body1" sx={{ mb: 2 }}>
          {selectedTool.description}
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle1" gutterBottom>
          Return Value
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          {selectedTool.return_description || "No return description provided"}
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Typography variant="h6" gutterBottom>
          Parameters
        </Typography>

        {/* Handle both toolParams and toolMetadata.args as parameter sources */}
        <ToolParamsForm
          params={
            toolParams[selectedTool.name] ||
            (selectedTool.args
              ? selectedTool.args.reduce(
                  (acc: Record<string, any>, arg: any) => {
                    acc[arg.name] = {
                      type: arg.type,
                      has_default: arg.has_default || false,
                      default: arg.default || null,
                      description: arg.description || "",
                      example: arg.example_value || null,
                    };
                    return acc;
                  },
                  {},
                )
              : {})
          }
          values={paramValues}
          onChange={handleParamChange}
          readOnly={!isRunnable}
        />

        {isRunnable && toolReturnValue !== null && (
          <Box sx={{ mt: 3, mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Tool Return Value
            </Typography>
            <Paper
              elevation={1}
              sx={{ p: 2, maxHeight: "400px", overflow: "auto" }}
            >
              {typeof toolReturnValue === "object" ? (
                <JSONView json={toolReturnValue} longTextWrap={true} />
              ) : (
                <Alert
                  severity="info"
                  sx={{
                    whiteSpace: "pre-wrap",
                    overflowWrap: "break-word",
                  }}
                >
                  {String(toolReturnValue)}
                </Alert>
              )}
            </Paper>
          </Box>
        )}

        {isRunnable && (
          <Box sx={{ mt: 3, display: "flex", justifyContent: "flex-end" }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PlayArrowIcon />}
              onClick={handleExecuteTool}
              disabled={isExecuting}
            >
              {isExecuting ? "Executing..." : "Execute Tool"}
            </Button>
          </Box>
        )}
      </Box>
    </Paper>
  );
}

export default ToolInfo;

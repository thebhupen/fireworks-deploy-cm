// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Autocomplete,
  Card,
  CardContent,
  TextField,
  Typography,
  Box,
} from "@mui/material";
import * as React from "react";
import { useState, useCallback } from "react";
import { useAppContext } from "../contexts/AppContextProvider";
import { AppViews, ToolMetadataType } from "../utils/types";
import { stripAppNamePrefix } from "../utils/toolUtils";
import ToolInfoComponent from "./ToolInfo";

/**
 * AppsToolsInfo component displays information about the tools available from a specific app.
 * It provides a typeahead dropdown to select a specific tool and view its details.
 *
 * @param appName - The name of the app to display tool information for
 * @returns React component displaying tool information
 */
function AppsToolsInfo({ appName }: { appName: string }): React.ReactNode {
  const { appNameToToolsMap, appNameToToolParamsMap, appView } =
    useAppContext();
  const isPlaygroundView = appView === AppViews.PLAYGROUND;
  const [selectedTool, setSelectedTool] = useState<ToolMetadataType | null>(
    null,
  );

  // Convert original tools to ToolMetadataType[]
  const originalTools = appNameToToolsMap.get(appName) || [];
  const tools: ToolMetadataType[] = originalTools.map((tool: any) => ({
    name: tool.name,
    description: tool.description,
    args: (tool.args || []).map((arg: any) => ({
      name: arg.name,
      type: arg.type,
      description: arg.description || "",
    })),
    return_type: tool.return_type || null,
    return_description: tool.return_description || null,
    write_operation: tool.write_operation,
  }));
  const toolParams = appNameToToolParamsMap.get(appName) || {};

  const handleToolChange = useCallback(
    (_event: any, newValue: ToolMetadataType | null) => {
      setSelectedTool(newValue);
    },
    [],
  );

  if (tools.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body1">
            No tools available for {appName}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Tools for {appName}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {tools.length} tool{tools.length !== 1 ? "s" : ""} available
        </Typography>

        <Box sx={{ mt: 2, mb: 3 }}>
          <Autocomplete
            id="tool-selector"
            options={tools as any}
            getOptionLabel={(option) =>
              stripAppNamePrefix(option.name, appName)
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Select a tool"
                variant="outlined"
                placeholder="Start typing to search tools..."
              />
            )}
            renderOption={(props, option) => (
              <Box component="li" {...props}>
                <Box>
                  <Typography variant="body1">
                    {stripAppNamePrefix(option.name, appName)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {option.description.length > 100
                      ? `${option.description.substring(0, 100)}...`
                      : option.description}
                  </Typography>
                </Box>
              </Box>
            )}
            onChange={handleToolChange as any}
            value={selectedTool as any}
            isOptionEqualToValue={(option, value) => option.name === value.name}
            fullWidth
          />
        </Box>

        {selectedTool && (
          <ToolInfoComponent
            selectedTool={selectedTool}
            appName={appName}
            isRunnable={isPlaygroundView}
            toolParams={toolParams}
          />
        )}

        {!selectedTool && (
          <Box
            sx={{
              mt: 2,
              p: 3,
              textAlign: "center",
              bgcolor: "background.paper",
            }}
          >
            <Typography variant="body1" color="text.secondary">
              Select a tool from the dropdown to view its details
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default AppsToolsInfo;

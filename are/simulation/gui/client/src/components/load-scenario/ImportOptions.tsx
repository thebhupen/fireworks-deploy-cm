// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Box, Checkbox, FormControlLabel, Typography } from "@mui/material";

interface ImportOptionsProps {
  replayLogs: boolean;
  onReplayLogsChange: (value: boolean) => void;
}

const ImportOptions = ({
  replayLogs,
  onReplayLogsChange,
}: ImportOptionsProps) => {
  return (
    <Box
      sx={{
        mt: 1,
        p: 2,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
        Options
      </Typography>
      <FormControlLabel
        control={
          <Checkbox
            checked={replayLogs}
            onChange={(e) => onReplayLogsChange(e.target.checked)}
            size="small"
            sx={{
              color: "primary.main",
              "&.Mui-checked": {
                color: "primary.main",
              },
            }}
          />
        }
        label={
          <Box>
            <Typography variant="body2">Import Completed Events</Typography>
            <Typography variant="caption" color="text.secondary">
              Include events that have already been processed from the log file.
            </Typography>
          </Box>
        }
        sx={{
          alignItems: "flex-start",
          ml: 0,
          "& .MuiFormControlLabel-label": {
            ml: 1,
          },
        }}
      />
    </Box>
  );
};

export default ImportOptions;

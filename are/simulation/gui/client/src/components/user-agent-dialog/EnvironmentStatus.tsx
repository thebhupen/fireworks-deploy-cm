// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Box, CircularProgress, Typography, useTheme } from "@mui/material";
import { Stack } from "@mui/system";
import { AnimatePresence, motion } from "motion/react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { EnvState } from "../../utils/types";
import { AgentLoadingIndicator } from "./AgentLoadingIndicator";

interface EnvironmentStatusProps {
  isAgentRunning: boolean;
}

const EnvironmentStatus = ({ isAgentRunning }: EnvironmentStatusProps) => {
  const { envState } = useAppContext();
  const theme = useTheme();

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: isAgentRunning || envState === EnvState.STOPPED ? "36px" : 0,
        display: "flex",
        alignItems: "center",
        overflow: "hidden",
        marginTop: 3,
        marginBottom: isAgentRunning || envState === EnvState.STOPPED ? 3 : 0,
      }}
    >
      <AnimatePresence>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            marginX: 5,
          }}
        >
          {isAgentRunning ? <AgentLoadingIndicator /> : <div />}
          {envState === EnvState.STOPPED ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ width: "100%", textAlign: "center" }}
              transition={{ duration: 0.5 }}
            >
              <Stack spacing={2} direction="row" alignItems="center">
                <Box
                  sx={{
                    width: "100%",
                    borderTop: `1px solid ${theme.palette.divider}`,
                    minHeight: "1px",
                  }}
                />
                <Typography
                  color="textDisabled"
                  fontWeight="bold"
                  sx={{ whiteSpace: "nowrap" }}
                >
                  Scenario stopped
                </Typography>
                <Box
                  sx={{
                    width: "100%",
                    borderTop: `1px solid ${theme.palette.divider}`,
                    minHeight: "1px",
                  }}
                />
              </Stack>
            </motion.div>
          ) : (
            isAgentRunning && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  color: theme.palette.text.secondary,
                }}
              >
                <CircularProgress size={12} color="inherit" />
              </motion.div>
            )
          )}
        </Box>
      </AnimatePresence>
    </Box>
  );
};

export default EnvironmentStatus;

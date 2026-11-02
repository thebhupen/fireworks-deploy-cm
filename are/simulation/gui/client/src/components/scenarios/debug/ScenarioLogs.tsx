// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ManageSearchIcon from "@mui/icons-material/ManageSearch";
import { Stack, Typography, useTheme } from "@mui/material";
import { AnimatePresence, motion } from "motion/react";
import { useAppContext } from "../../../contexts/AppContextProvider";
import { AgentLogsSection } from "../../agent-logs/AgentLogsSection";
import DebugCard from "./DebugCard";
import ViewModeToggle, { ViewMode } from "./ViewModeToggle";

interface ScenarioLogsProps {
  viewMode: ViewMode;
  onViewModeChange: (
    event: React.MouseEvent<HTMLElement>,
    newViewMode: ViewMode | null,
  ) => void;
}

const ScenarioLogs = ({ viewMode, onViewModeChange }: ScenarioLogsProps) => {
  const { worldLogs } = useAppContext();
  const theme = useTheme();

  return (
    <>
      <DebugCard
        title="Logs"
        menu={
          <ViewModeToggle
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
          />
        }
        actions={worldLogs.length > 0 ? null : <div />}
      >
        <AnimatePresence>
          {worldLogs.length > 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ width: "100%" }}
            >
              <AgentLogsSection worldLogs={worldLogs} showHeader={false} />
            </motion.div>
          ) : (
            <Stack
              width={"100%"}
              height={"100%"}
              justifyContent={"center"}
              alignItems={"center"}
              spacing={1}
            >
              <ManageSearchIcon
                htmlColor={theme.palette.text.disabled}
                fontSize="large"
              />
              <Typography color="text.disabled">No logs</Typography>
            </Stack>
          )}
        </AnimatePresence>
      </DebugCard>
    </>
  );
};

export default ScenarioLogs;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { ReactNode } from "react";

// Enum for view modes
export enum ViewMode {
  Events = "events",
  Logs = "logs",
}

interface ViewModeToggleProps {
  viewMode: ViewMode;
  onViewModeChange: (
    event: React.MouseEvent<HTMLElement>,
    newViewMode: ViewMode | null,
  ) => void;
}

/**
 * Toggle button group for switching between Events and Agent Log views
 */
const ViewModeToggle = ({
  viewMode,
  onViewModeChange,
}: ViewModeToggleProps): ReactNode => {
  return (
    <ToggleButtonGroup
      value={viewMode}
      exclusive
      onChange={onViewModeChange}
      aria-label="view mode"
      size="small"
      sx={{ marginRight: 0.5 }}
    >
      <ToggleButton
        value={ViewMode.Events}
        size="small"
        aria-label="events view"
      >
        Events
      </ToggleButton>
      <ToggleButton value={ViewMode.Logs} size="small" aria-label="logs view">
        Agent
      </ToggleButton>
    </ToggleButtonGroup>
  );
};

export default ViewModeToggle;

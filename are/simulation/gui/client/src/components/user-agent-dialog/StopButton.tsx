// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { IconButton } from "@mui/material";
import StopIcon from "@mui/icons-material/Stop";

function StopButton({
  isRunning,
  onClick,
}: {
  isRunning: boolean;
  onClick?:
    | (((event: React.MouseEvent<HTMLElement, MouseEvent>) => void) &
        React.MouseEventHandler<HTMLButtonElement>)
    | undefined;
}): React.ReactNode {
  return (
    <IconButton
      size="small"
      sx={{
        color: "rgb(205, 66, 70)",
      }}
      color="inherit"
      disabled={!isRunning}
      onClick={onClick}
    >
      <StopIcon />
    </IconButton>
  );
}

export default StopButton;

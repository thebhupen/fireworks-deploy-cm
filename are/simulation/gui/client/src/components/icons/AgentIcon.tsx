// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import SmartToyIcon from "@mui/icons-material/SmartToy";
import { Box, useTheme } from "@mui/material";
import { ReactNode } from "react";

export function AgentIcon({
  children,
  size = 32,
}: {
  children?: ReactNode;
  size?: number;
}) {
  const theme = useTheme();
  return (
    <Box
      sx={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
        flexShrink: 0,
        flexGrow: 0,
        borderRadius: "50%",
      }}
    >
      <SmartToyIcon htmlColor={theme.palette.lightgrey.main} />
      {children}
    </Box>
  );
}

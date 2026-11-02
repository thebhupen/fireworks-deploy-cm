// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { alpha, Typography, useTheme } from "@mui/material";
import Box from "@mui/material/Box";
import { useAppContext } from "../../contexts/AppContextProvider";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import { ThoughtMessageType } from "./createMessageList";

export default function ThoughtMessage({
  message,
}: {
  message: ThoughtMessageType;
}) {
  const theme = useTheme();
  const { infoLevel } = useAppContext();
  const showTimestamps = infoLevel.timestamps === true;

  return (
    <Box
      sx={{
        display: "flex",
        color: theme.palette.text.secondary,
        marginLeft: 5,
        marginRight: 5,
        alignItems: "center",
        borderLeft: `1px solid ${theme.palette.divider}`,
        paddingLeft: 2,
        paddingY: 0.5,
        maxWidth: "85%",
      }}
    >
      <Typography variant="body2">
        <strong>Thought: </strong>
        <span>
          {showTimestamps && (
            <span style={{ color: alpha(theme.palette.text.secondary, 0.8) }}>
              {formatDateAndTimeFromTime(message.timestamp * 1000)}
            </span>
          )}{" "}
          {message.content.replace(/^Thought:\s/g, "")}
        </span>
      </Typography>
    </Box>
  );
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import Box from "@mui/material/Box";
import { PlanMessageType } from "./createMessageList";
import Markdown from "react-markdown";
import { useTheme } from "@mui/material";
import { lighten } from "@mui/system";

export default function PlanMessage({ message }: { message: PlanMessageType }) {
  const theme = useTheme();

  if (message.content == null) {
    return null;
  }

  const content = message.content.replace("```", "");
  const formattedContent = `# Plan\n${content || ""}\n`;

  return (
    <Box
      sx={{
        display: "flex",
        color: theme.palette.text.secondary,
        fontSize: 12,
        marginLeft: "36px",
        flexDirection: "column",
        border: `1px solid ${lighten(theme.palette.text.secondary, 0.3)}`, // Lightened border color
        borderRadius: "4px", // Optional: rounded corners
        padding: "10px", // Optional: adds spacing inside the box
        marginTop: "15px", // Optional: adds spacing between the boxes
        marginBottom: "15px", // Optional: adds spacing between the boxes
      }}
    >
      <Markdown>{formattedContent}</Markdown>
    </Box>
  );
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Stack, useTheme } from "@mui/material";
import { LLMInputOutputType } from "./createMessageList";

export function LLMInputOutputMessage({
  message,
}: {
  message: LLMInputOutputType;
}) {
  const theme = useTheme();

  if (!message.output) {
    return null;
  }

  return (
    <Stack
      gap={1}
      sx={{
        marginLeft: 4,
        marginBottom: 1.5,
        marginTop: 1.5,
        color: theme.palette.text.secondary,
      }}
    >
      {message.output && (
        <Stack
          direction="row"
          alignItems="center"
          gap={1}
          sx={{
            fontSize: 12,
            marginLeft: 1,
          }}
        >
          Worked for {message.duration?.toFixed(2)} seconds
        </Stack>
      )}
    </Stack>
  );
}

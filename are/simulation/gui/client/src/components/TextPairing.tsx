// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Stack, Typography } from "@mui/material";

export function TextPairing({
  heading,
  description,
}: {
  heading: string;
  description: string;
}) {
  return (
    <Stack>
      <Typography fontWeight="bold">{heading}</Typography>
      <Typography>{description}</Typography>
    </Stack>
  );
}

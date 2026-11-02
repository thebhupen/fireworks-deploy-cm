// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Card, Stack, useTheme } from "@mui/material";
import Box from "@mui/material/Box";
import ButtonBase from "@mui/material/ButtonBase";
import Drawer from "@mui/material/Drawer";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import type { ErrorMessage } from "./createMessageList";

export default function ErrorMessage({ message }: { message: ErrorMessage }) {
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const theme = useTheme();

  return (
    <>
      <Drawer
        anchor="right"
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
        }}
        slotProps={{
          paper: {
            sx: {
              width: "50%",
              maxWidth: 1000,
              padding: 4,
            },
          },
        }}
      >
        <Stack spacing={1} height={"100%"}>
          <Typography variant="h5">{message.content}</Typography>
          <Card
            variant="outlined"
            sx={{ padding: 2, height: "100%", overflowY: "auto" }}
          >
            <Typography fontFamily={"monospace"}>{message.error}</Typography>
          </Card>
        </Stack>
      </Drawer>
      <ButtonBase
        sx={{
          marginLeft: 5,
          marginRight: 5,
          maxWidth: "85%",
          color: theme.palette.error.main,
          fontSize: 13,
          marginTop: 0,
          padding: 1,
          borderTopRightRadius: 4,
          borderBottomRightRadius: 4,
          backgroundColor: `${theme.palette.error.main}10`,
          borderLeft: `1px solid ${theme.palette.error.main}`,
          display: "inline-block",
          width: "100%",
          paddingLeft: 2,
        }}
        onClick={() => setIsDrawerOpen(true)}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <strong>Error: </strong>
          {message.content}
        </Box>
      </ButtonBase>
    </>
  );
}

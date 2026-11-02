// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { IconButton } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import commitPlay from "../../mutations/PlayMutation";
import { useRelayEnvironment } from "react-relay";
import { useNotifications } from "../../contexts/NotificationsContextProvider";

function PlayButton({
  isRunning,
  sessionId,
}: {
  isRunning: boolean;
  sessionId: string;
}): React.ReactNode {
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();

  return (
    <IconButton
      size="small"
      sx={{
        color: "rgb(0, 122, 255)",
      }}
      color="inherit"
      disabled={isRunning}
      onClick={() => {
        commitPlay(environment, sessionId, notify);
      }}
    >
      <PlayArrowIcon />
    </IconButton>
  );
}

export default PlayButton;

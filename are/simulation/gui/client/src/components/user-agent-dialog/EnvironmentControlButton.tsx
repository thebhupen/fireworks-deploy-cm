// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import RestartAltIcon from "@mui/icons-material/RestartAlt";
import StopIcon from "@mui/icons-material/Stop";
import { IconButton, Tooltip, useTheme } from "@mui/material";
import { useContext } from "react";
import { useMutation } from "react-relay";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../contexts/SessionIdContext";
import { LoadMutation } from "../../mutations/LoadMutation";
import { StopMutation } from "../../mutations/StopMutation";
import { EnvState } from "../../utils/types";

export function EnvironmentControlButton() {
  const {
    eventLog,
    envState,
    localEnvState,
    setLocalEnvState,
    isResettingScenario,
    setIsResettingScenario,
  } = useAppContext();
  const sessionId = useContext(SessionIdContext);
  const [commitStop] = useMutation(StopMutation);
  const [commitLoad] = useMutation(LoadMutation);
  const { notify } = useNotifications();
  const theme = useTheme();

  const handleStop = () => {
    setLocalEnvState(EnvState.STOPPED);
    commitStop({
      variables: {
        sessionId,
      },
      onCompleted: () => {},
      onError: (error) => {
        setLocalEnvState(envState);
        console.error(`Error stopping scenario: ${error.message}`);
        notify({
          type: "error",
          message: "Error stopping scenario",
        });
      },
    });
  };

  const handleReset = () => {
    setIsResettingScenario(true);
    setLocalEnvState(EnvState.SETUP);
    commitLoad({
      variables: {
        sessionId,
      },
      onCompleted: () => {
        setIsResettingScenario(false);
      },
      onError: (error) => {
        setIsResettingScenario(false);
        setLocalEnvState(envState);
        console.error(`Error resetting scenario: ${error.message}`);
        notify({
          type: "error",
          message: "Error resetting scenario",
        });
      },
    });
  };

  return (
    <>
      {["RUNNING", "PAUSED", "FAILED"].includes(localEnvState) ? (
        <Tooltip title="Stop scenario">
          <span>
            <IconButton
              size="small"
              color="error"
              onClick={() => handleStop()}
              sx={{
                bgcolor: `${theme.palette.lightgrey.main}`,
                opacity: 1,
                "&:hover": {
                  bgcolor: `${theme.palette.lightgrey.main}`,
                  opacity: 0.5,
                },
                transition: "opacity 0.2s",
              }}
            >
              <StopIcon />
            </IconButton>
          </span>
        </Tooltip>
      ) : (
        <Tooltip
          title={
            isResettingScenario ? "Resetting scenario..." : "Reload scenario"
          }
        >
          <span>
            <IconButton
              size="small"
              onClick={() => handleReset()}
              disabled={
                isResettingScenario ||
                !localEnvState ||
                ((localEnvState === EnvState.SETUP ||
                  envState === EnvState.SETUP) &&
                  eventLog.length === 0)
              }
              color="darkgrey"
              sx={{
                bgcolor: `${theme.palette.lightgrey.main}`,
                opacity: 1,
                "&:hover": {
                  bgcolor: `${theme.palette.lightgrey.main}`,
                  opacity: 0.5,
                },
              }}
            >
              <RestartAltIcon />
            </IconButton>
          </span>
        </Tooltip>
      )}
    </>
  );
}

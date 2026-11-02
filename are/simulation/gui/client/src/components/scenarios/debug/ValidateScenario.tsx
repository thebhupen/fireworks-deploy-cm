// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import AlarmIcon from "@mui/icons-material/Alarm";
import PauseIcon from "@mui/icons-material/Pause";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import RuleIcon from "@mui/icons-material/Rule";
import SpeedIcon from "@mui/icons-material/Speed";
import StopIcon from "@mui/icons-material/Stop";
import {
  Box,
  Fab,
  IconButton,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useContext, useEffect, useState } from "react";
import { useMutation } from "react-relay";
import { useAppContext } from "../../../contexts/AppContextProvider";
import { useNotifications } from "../../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../../contexts/SessionIdContext";
import { LoadMutation } from "../../../mutations/LoadMutation";
import { PauseMutation } from "../../../mutations/PauseMutation";
import { PlayMutation } from "../../../mutations/PlayMutation";
import { StopMutation } from "../../../mutations/StopMutation";
import { EnvState } from "../../../utils/types";
import { ChatSection } from "../../user-agent-dialog/ChatSection";
import { InfoLevelMenu } from "../../user-agent-dialog/InfoLevelMenu";
import DurationDialog from "../DurationDialog";
import TimeIncrementDialog from "../TimeIncrementDialog";
import DebugCard from "./DebugCard";

const ValidateScenario = () => {
  const {
    envState,
    localEnvState,
    setLocalEnvState,
    scenario,
    infoLevel,
    setInfoLevel,
  } = useAppContext();
  const sessionId = useContext(SessionIdContext);
  const theme = useTheme();
  const isUndefined = envState === undefined;
  const isStopped = !isUndefined && envState === EnvState.STOPPED;
  const isSetup = !isUndefined && envState === EnvState.SETUP;
  const isPaused = !isUndefined && envState === EnvState.PAUSED;

  const [duration, setDuration] = useState<number | null>(
    scenario?.duration ?? null,
  );
  const [timeIncrement, setTimeIncrement] = useState<number | null>(
    scenario?.timeIncrementInSeconds ?? 1,
  );

  const [isEditDurationDialogOpen, setIsEditDurationDialogOpen] =
    useState(false);
  const [isEditTimeIncrementDialogOpen, setIsEditTimeIncrementDialogOpen] =
    useState(false);
  const { notify } = useNotifications();
  const [commitPlay] = useMutation(PlayMutation);
  const [commitPause, isPauseInFlight] = useMutation(PauseMutation);
  const [commitStop] = useMutation(StopMutation);
  const [commitLoad] = useMutation(LoadMutation);

  const handlePlay = () => {
    setLocalEnvState(EnvState.RUNNING);
    commitPlay({
      variables: {
        sessionId,
      },
      onCompleted: () => {},
      onError: (error) => {
        setLocalEnvState(envState);
        console.error(`Error starting scenario: ${error.message}`);
        notify({
          type: "error",
          message: "Error starting scenario",
        });
      },
    });
  };

  const handlePause = () => {
    setLocalEnvState(EnvState.PAUSED);
    commitPause({
      variables: {
        sessionId,
      },
      onCompleted: () => {},
      onError: (error) => {
        setLocalEnvState(envState);
        console.error(`Error pausing scenario: ${error.message}`);
        notify({
          type: "error",
          message: "Error pausing scenario",
        });
      },
    });
  };

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
    setLocalEnvState(EnvState.SETUP);
    commitLoad({
      variables: {
        sessionId,
      },
      onCompleted: () => {},
      onError: (error) => {
        setLocalEnvState(envState);
        console.error(`Error resetting scenario: ${error.message}`);
        notify({
          type: "error",
          message: "Error resetting scenario",
        });
      },
    });
  };

  useEffect(() => {
    setLocalEnvState(envState);
  }, [envState]);

  // Force timestamps to be enabled when ValidateScenario is open
  useEffect(() => {
    const initialTimestampsValue = infoLevel.timestamps;
    setInfoLevel((prevInfoLevel) => ({ ...prevInfoLevel, timestamps: true }));
    return () => {
      setInfoLevel((prevInfoLevel) => ({
        ...prevInfoLevel,
        timestamps: initialTimestampsValue,
      }));
    };
  }, [setInfoLevel]);

  // Update duration and timeIncrement from scenario
  useEffect(() => {
    if (scenario) {
      setDuration(scenario.duration ?? null);
      setTimeIncrement(scenario.timeIncrementInSeconds ?? 1);
    }
  }, [scenario]);

  return (
    <>
      <DebugCard
        title="Run scenario"
        menu={<InfoLevelMenu color={theme.palette.text.secondary} />}
        actions={
          <Box
            sx={{
              backgroundColor: "#333",
              paddingX: 1.5,
              paddingY: 0.75,
              borderRadius: "8px",
            }}
          >
            <Stack direction="row" spacing={1} alignItems="center">
              {["RUNNING", "PAUSED", "FAILED"].includes(localEnvState) ? (
                <Tooltip title="Stop scenario">
                  <IconButton
                    size="small"
                    color="error"
                    sx={{ border: `1px solid ${theme.palette.error.main}` }}
                    onClick={() => handleStop()}
                  >
                    <StopIcon fontSize="inherit" />
                  </IconButton>
                </Tooltip>
              ) : (
                <Tooltip title="Reload scenario">
                  <span>
                    <IconButton
                      size="small"
                      color="primary"
                      sx={{
                        border: `1px solid ${isStopped ? theme.palette.primary.main : theme.palette.divider}`,
                      }}
                      onClick={() => handleReset()}
                      disabled={localEnvState === "SETUP"}
                    >
                      <RestartAltIcon fontSize="inherit" />
                    </IconButton>
                  </span>
                </Tooltip>
              )}
              {localEnvState === "RUNNING" ? (
                <Tooltip title={"Pause scenario"}>
                  <Fab
                    size="small"
                    color="primary"
                    onClick={() => handlePause()}
                    disabled={isPauseInFlight && !isPaused}
                    sx={{
                      zIndex: 2,
                    }}
                  >
                    {<PauseIcon />}
                  </Fab>
                </Tooltip>
              ) : (
                <Tooltip title={"Run Scenario"}>
                  <Fab
                    size="small"
                    color="primary"
                    onClick={() => handlePlay()}
                    disabled={!["PAUSED", "SETUP"].includes(localEnvState)}
                    sx={{
                      zIndex: 2,
                    }}
                  >
                    {<PlayArrowIcon />}
                  </Fab>
                </Tooltip>
              )}
              <Stack direction="row" spacing={1} alignItems="center">
                <Tooltip title="Set Duration">
                  <IconButton
                    size="small"
                    color="lightgrey"
                    sx={{ border: `1px solid ${theme.palette.divider}` }}
                    onClick={() => {
                      setIsEditDurationDialogOpen(true);
                    }}
                  >
                    <AlarmIcon fontSize="inherit" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Set Time Increment">
                  <IconButton
                    size="small"
                    color="lightgrey"
                    sx={{ border: `1px solid ${theme.palette.divider}` }}
                    onClick={() => {
                      setIsEditTimeIncrementDialogOpen(true);
                    }}
                  >
                    <SpeedIcon fontSize="inherit" />
                  </IconButton>
                </Tooltip>
                <Typography
                  color={
                    isUndefined || isSetup || isStopped
                      ? "textDisabled"
                      : "textPrimary"
                  }
                >
                  {`${duration && duration > 0 ? `${duration}s` : "Unset"}${timeIncrement && timeIncrement > 1 ? ` (${timeIncrement}s/tick)` : ""}`}
                </Typography>
              </Stack>
            </Stack>
          </Box>
        }
      >
        {isUndefined || isSetup ? (
          <Stack
            width={"100%"}
            height={"100%"}
            justifyContent={"center"}
            alignItems={"center"}
            spacing={1}
          >
            <RuleIcon
              htmlColor={theme.palette.text.disabled}
              fontSize="large"
            />
            <Typography color="text.disabled">No scenario running</Typography>
          </Stack>
        ) : (
          <ChatSection input={null} header={null} />
        )}
      </DebugCard>
      <DurationDialog
        isOpen={isEditDurationDialogOpen}
        setIsOpen={setIsEditDurationDialogOpen}
        duration={duration}
        setDuration={setDuration}
      />
      <TimeIncrementDialog
        isOpen={isEditTimeIncrementDialogOpen}
        setIsOpen={setIsEditTimeIncrementDialogOpen}
        timeIncrement={timeIncrement}
        setTimeIncrement={setTimeIncrement}
      />
    </>
  );
};

export default ValidateScenario;

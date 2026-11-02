// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import Box from "@mui/material/Box";

import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { CircularProgress, Stack, Typography, useTheme } from "@mui/material";
import React, { useEffect, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import { getAppNameFromToolName } from "../../utils/toolUtils";
import { AppName } from "../../utils/types";
import AppIcon from "../icons/AppIcon";
import { ActionMessageType } from "./createMessageList";

export default function Actionmessage({
  message,
}: {
  message: ActionMessageType;
}) {
  const { setSelectedApp, infoLevel } = useAppContext();
  const [hasWaitedLong, setHasWaitedLong] = useState(true);
  const theme = useTheme();
  const showTimestamps = infoLevel.timestamps === true;

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setHasWaitedLong(false);
    }, 120000);
    return () => clearTimeout(timeoutId);
  }, []);

  const openApp = () => {
    // If toolMetadata is available, use its name for the app name
    // This ensures we open the correct app in the drawer
    const appName =
      getAppNameFromToolName(message.toolMetadata?.name) || message.appName;

    setSelectedApp(appName as AppName, {
      extraData: {
        name: "App Function Call",
        data: {
          app: message.appName,
          action: message.actionName,
          input: message.input,
          output: message.output,
          exception: message.exception,
          stackTrace: message.exceptionStackTrace,
          toolMetadata: message.toolMetadata,
        },
      },
    });
  };

  return (
    <Stack
      spacing={1}
      sx={{
        marginLeft: 5,
        marginRight: 5,
        maxWidth: "85%",
      }}
    >
      <Box
        sx={{
          display: "flex",
          color: theme.palette.text.secondary,
          alignItems: "center",
          borderLeft: `1px solid ${theme.palette.divider}`,
          borderTopRightRadius: 4,
          borderBottomRightRadius: 4,
          paddingLeft: 2,
          paddingY: 0.5,
          cursor: "pointer",
          "&:hover": {
            backgroundColor: `${theme.palette.action.hover}`,
          },
          transition: "background-color 0.2s",
        }}
        onClick={() => {
          openApp();
        }}
      >
        <Box
          sx={{
            display: "flex",
            width: "100%",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Box display="inline-flex">
            <Typography variant="body2" sx={{ fontWeight: "bold" }}>
              Action:
            </Typography>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ marginLeft: 1 }}
            >
              <AppIcon
                appName={message.appName}
                size={12}
                color={theme.palette.text.primary}
              />
              {showTimestamps && (
                <Typography
                  variant="body2"
                  component="span"
                  sx={{ opacity: 0.8 }}
                >
                  {formatDateAndTimeFromTime(message.timestamp * 1000)}
                </Typography>
              )}
              <Typography variant="body2" component="span">
                {message.appName} {message.actionName}
              </Typography>
            </Stack>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", paddingRight: 2 }}>
            <LoadingIndicator
              hasWaitedLong={hasWaitedLong}
              completed={message.completed}
              hasException={message.exception != null}
            />
          </Box>
        </Box>
      </Box>
      {message.exception && infoLevel.errors && (
        <Box
          sx={{
            color: theme.palette.error.main,
            fontSize: 13,
            marginTop: 0,
            marginLeft: 4,
            padding: 1,
            borderTopRightRadius: 4,
            borderBottomRightRadius: 4,
            backgroundColor: `${theme.palette.error.main}10`,
            borderLeft: `1px solid ${theme.palette.error.main}`,
            display: "inline-block",
            width: "100%",
            paddingLeft: 2,
          }}
        >
          <strong>Error: </strong>
          {message.exception}
        </Box>
      )}
    </Stack>
  );
}

function LoadingIndicator({
  hasWaitedLong,
  completed,
  hasException,
}: {
  hasWaitedLong: boolean;
  completed: boolean;
  hasException: boolean;
}): React.ReactNode {
  if (hasException) {
    return (
      <ErrorIcon sx={{ width: 18, height: 18, color: "white" }} color="error" />
    );
  } else if (completed) {
    return (
      <CheckCircleIcon
        sx={{ width: 18, height: 18, color: "white" }}
        color="success"
      />
    );
  } else if (hasWaitedLong && completed === false) {
    return <CircularProgress size={18} />;
  } else {
    return <WarningAmberIcon sx={{ width: 18, height: 18 }} color="warning" />;
  }
}

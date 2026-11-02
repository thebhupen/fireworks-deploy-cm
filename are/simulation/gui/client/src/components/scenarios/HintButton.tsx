// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { useContext, useEffect } from "react";

import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, Button, Popover, TextField, Typography } from "@mui/material";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../contexts/SessionIdContext";
import commitEditHintContent from "../../mutations/EditEventHintMutation";
import useRelayEnvironment from "../../relay/RelayEnvironment";
import { Hint, HintStatus } from "../../utils/types";

const PLACEHOLDER = `Please fill this with the steps required to solve the task, as if you were teaching a student:

- Only address the part of the task between the current ENV event or send_message_to_agent, and the next ENV event or send_message_to_agent.
- Include read actions.

Example:

1) Hint in send_message_to_agent containing initial task

  1. Note that today is 1/23/2022 which means tomorrow is 1/24.
  2. Add an event to the calendar titled 'Yoga Class' from 7 to 8 PM on 1/24.
  3. Find the ID of the email from Kaito Nakamura about visiting Tokyo using the email app.
  4976ea102f0140f7b621fcabe6b54416
  4. Reply to Kaito Nakamura's email regarding visiting Tokyo asking him if he is available to meetl from 4 to 5 PM on Tuesday, 1/25.

2) Hint in ENV event (e.g. after send_message received from Kaito)

  1. Add an event to the calendar titled 'Meeting with Kaito' from 4 to 5 PM on 1/25.
  2. Book a standard cab ride from Home to the meeting place Kaito gave at 3:30 PM on 1/25 using the Cab app.`;

interface Props {
  hint: Hint;
  taskContent?: string;
  hintsStatus: Map<string, HintStatus>;
  setHintsStatus: React.Dispatch<React.SetStateAction<Map<string, HintStatus>>>;
}

export default function HintButton({
  hint,
  taskContent,
  hintsStatus,
  setHintsStatus,
}: Props): React.ReactNode {
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const [hasUncommitContent, setHasUncommitContent] =
    React.useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = React.useState<boolean>(false);
  const [anchor, setAnchor] = React.useState<null | HTMLElement>(null);
  const [hintContext, setHintContext] = React.useState<string>(hint.content);
  const { notify } = useNotifications();
  const color = hintsStatus.get(hint.associatedEventId) || HintStatus.Error;
  const icon =
    hint.content.length > 0 ? (
      !hasUncommitContent ? (
        <CheckCircleOutlineIcon />
      ) : (
        <WarningAmberIcon />
      )
    ) : (
      <ErrorOutlineIcon />
    );
  const tooltip =
    hint.content.length > 0
      ? !hasUncommitContent
        ? "Completed"
        : "Unsaved Changes"
      : "No Hints Available";

  useEffect(() => {
    const newStatus =
      hintContext.length > 0
        ? hasUncommitContent
          ? HintStatus.Warning
          : HintStatus.Success
        : HintStatus.Error;
    setHintsStatus((prev) =>
      new Map(prev).set(hint.associatedEventId, newStatus),
    );
  }, [hintContext, hasUncommitContent, hint.associatedEventId, setHintsStatus]);

  const handleSubmit = async () => {
    setAnchor(null);
    await commitEditHintContent(
      environment,
      hint.associatedEventId, // Assuming this is the eventId
      hintContext, // Assuming this is the hintContent
      sessionId,
      notify,
    );
    setHasUncommitContent(false);
    setIsSubmitting(false);
  };

  return (
    <>
      <Tooltip title={tooltip}>
        <IconButton
          size="small"
          aria-label="hints"
          disabled={isSubmitting}
          onClick={(event) => {
            setAnchor(event.currentTarget);
          }}
          color={color}
        >
          {icon}
        </IconButton>
      </Tooltip>
      <Popover
        open={anchor != null}
        anchorEl={anchor}
        onClose={() => {
          setAnchor(null);
        }}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "8px",
            maxWidth: 600,
          }}
        >
          <Typography>Event ID: {hint.associatedEventId}</Typography>
          {taskContent && <Typography>Task Content: {taskContent}</Typography>}
          <TextField
            value={hintContext}
            onChange={(e) => {
              setHintContext(e.target.value);
              if (!hasUncommitContent) {
                setHasUncommitContent(true);
              }
            }}
            multiline
            className="textarea"
            placeholder={PLACEHOLDER}
          />
          <Button variant="contained" onClick={handleSubmit}>
            Submit
          </Button>
        </Box>
      </Popover>
    </>
  );
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useContext, useRef, useState } from "react";
import Markdown from "react-markdown";
import SessionIdContext from "../../contexts/SessionIdContext";
import commitSendConversationMessage from "../../mutations/SendConversationMessageMutation";
import useRelayEnvironment from "../../relay/RelayEnvironment";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SendIcon from "@mui/icons-material/Send";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import CopyToClipboard from "../common/CopyToClipboard";
import "./ConversationSection.css";
import { ConversationV2 } from "./types";

function ConversationSection({
  data,
  participants,
  messagingAppName,
  currentUserId,
}: {
  data: ConversationV2;
  participants: string[];
  messagingAppName: string;
  currentUserId?: string | null;
}) {
  // Use participant_ids (actual IDs) instead of participants (display strings)
  const participantIds = data.participant_ids || [];

  const sortedParticipantIds = participantIds.sort((a, b) => {
    const aIsCurrentUser = a === currentUserId || a.toLowerCase() === "me";
    const bIsCurrentUser = b === currentUserId || b.toLowerCase() === "me";

    if (aIsCurrentUser && !bIsCurrentUser) return -1;
    if (!aIsCurrentUser && bIsCurrentUser) return 1;
    return a.localeCompare(b);
  });

  const [newMessage, setNewMessage] = useState("");
  const [selectedParticipantId, setSelectedParticipantId] = useState(
    sortedParticipantIds[0],
  );
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();

  const handleSendMessage = () => {
    if (newMessage.trim() === "") {
      return;
    }

    // Convert "me" to actual currentUserId for backend
    const senderId =
      selectedParticipantId.toLowerCase() === "me"
        ? currentUserId || selectedParticipantId
        : selectedParticipantId;

    commitSendConversationMessage(
      environment,
      sessionId,
      messagingAppName,
      data.conversation_id!,
      senderId,
      newMessage,
      notify,
    );
    setNewMessage("");
  };

  const lastMessageRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleOpenConversation = () => {
    setTimeout(() => {
      lastMessageRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      inputRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 500);
  };

  return (
    <Accordion
      disableGutters
      onChange={(_, isExpanded) => {
        if (isExpanded) {
          handleOpenConversation();
        }
      }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack flexGrow={1} paddingY={2} paddingRight={2}>
          <Stack
            direction="row"
            justifyContent={"space-between"}
            alignItems={"center"}
          >
            <Typography fontWeight={"bold"}>{data.title}</Typography>
            <Typography variant="body2" color="textSecondary">
              {data.participants?.join(", ")}
            </Typography>
          </Stack>
          <Stack
            direction="row"
            justifyContent={"space-between"}
            alignItems={"center"}
          >
            <Stack direction="row" spacing={1} alignItems={"center"}>
              <Typography variant="body2">{data.conversation_id}</Typography>
              <CopyToClipboard value={data.conversation_id ?? ""} />
            </Stack>
            <Typography variant="body2" color="textSecondary">
              {data.last_updated
                ? formatDateAndTimeFromTime(data.last_updated * 1000)
                : ""}
            </Typography>
          </Stack>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Stack
          spacing={2}
          padding={2}
          sx={{ maxHeight: 500, overflowY: "scroll" }}
        >
          {data.messages
            ?.sort((a, b) => a.timestamp! - b.timestamp!)
            .map((message, index) => (
              <div
                key={index}
                ref={
                  index === (data.messages?.length ?? 0) - 1
                    ? lastMessageRef
                    : null
                }
                className={`message-bubble ${(message.sender_id && message.sender_id === currentUserId) || message.sender?.toLowerCase() === "me" ? "message-bubble-right" : "message-bubble-left"}`}
              >
                <div className="message-content">
                  <span className="message-sender">
                    {(message.sender_id &&
                      message.sender_id === currentUserId) ||
                    message.sender?.toLowerCase() === "me"
                      ? "Me"
                      : message.sender}
                  </span>
                  <span className="message-text">
                    <Markdown>{message.content}</Markdown>
                  </span>
                  <span className="message-timestamp">
                    {formatDateAndTimeFromTime(message.timestamp! * 1000)}
                  </span>
                </div>
              </div>
            ))}
        </Stack>
        <Stack direction="row" spacing={1} padding={2}>
          <FormControl size="small" fullWidth sx={{ maxWidth: 200 }}>
            <InputLabel>Act as</InputLabel>
            <Select
              value={selectedParticipantId}
              label="Act as"
              onChange={(e) => setSelectedParticipantId(e.target.value)}
            >
              {sortedParticipantIds.map((participantId, index) => {
                // Find the display name for this participant ID
                const displayName =
                  participants.find((p) => p.includes(`(${participantId})`)) ||
                  participantId;
                const isCurrentUser =
                  participantId === currentUserId ||
                  participantId.toLowerCase() === "me";

                return (
                  <MenuItem key={index} value={participantId}>
                    {isCurrentUser ? "User (me)" : displayName}
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
          <TextField
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSendMessage();
              }
            }}
            placeholder="Type your message..."
            autoFocus
            focused
            fullWidth
            size="small"
            inputRef={inputRef}
          />
          <Tooltip title="Send">
            <Button size="small" onClick={handleSendMessage}>
              <SendIcon />
            </Button>
          </Tooltip>
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}

export default ConversationSection;

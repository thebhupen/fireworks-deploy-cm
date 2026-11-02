// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  alpha,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  IconButton,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import * as React from "react";
import { useContext, useRef, useState } from "react";

import AttachFileIcon from "@mui/icons-material/AttachFile";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import EditIcon from "@mui/icons-material/Edit";
import { AnimatePresence, motion } from "motion/react";
import { useRelayEnvironment } from "react-relay";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../contexts/SessionIdContext";
import { deleteLogsAfterMutation } from "../../mutations/DeleteLogsAfterMutation";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";

import { getSessionRoot, normalizePath } from "../../utils/FileSystemUtils";
import { IMAGE_EXTENSION_REGEX } from "../../utils/fileUtils";

/**
 * Formats a message by:
 * 1. Removing "DETAILED_ANSWER" text
 * 2. Trimming attachment text that's automatically added by the server
 *    - Only if the message has attachments
 *    - Only trims the exact number of attachment lines that match the attachment count
 *    - Trims from the end of the message up
 */
function formatMessage(message: {
  content: string;
  attachments?: string[];
}): string {
  // First replace "DETAILED_ANSWER" text
  const formattedContent = message.content.replace("DETAILED_ANSWER", "");

  // Only process attachment text if the message has attachments
  if (!message.attachments || message.attachments.length === 0) {
    return formattedContent;
  }

  // Split the content into lines
  const lines = formattedContent.split("\n");

  // Count how many lines at the end match the attachment pattern
  const attachmentCount = message.attachments.length;
  let matchedAttachments = 0;
  let lastContentLineIndex = lines.length - 1;

  // Start from the end and work backwards
  for (let i = lines.length - 1; i >= 0; i--) {
    if (lines[i].trim().match(/^Attachment \d+:/)) {
      matchedAttachments++;
      lastContentLineIndex = i - 1; // The line before this attachment line

      // If we've found all the attachments we're looking for, stop
      if (matchedAttachments >= attachmentCount) {
        break;
      }
    }
  }

  // If we found attachment lines, trim them
  if (matchedAttachments > 0) {
    // Keep only the content up to the last content line
    return lines.slice(0, lastContentLineIndex + 1).join("\n");
  }

  // If no attachment text is found, return the content after replacing "DETAILED_ANSWER"
  return formattedContent;
}

export default function UserMessage({
  message,
  showTimestamps,
}: {
  message: {
    id: string;
    content: string;
    timestamp: number;
    attachments?: string[];
    isPending?: boolean;
    correlationId?: string | null;
  };
  showTimestamps: boolean;
}): React.ReactNode {
  // Check if this is a pending message
  const isPending = message.isPending === true;
  const theme = useTheme();
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();
  const [editing, setIsEditing] = useState(false);
  const [edit, setEdit] = useState(message.content);
  const inputFieldRef = useRef<HTMLTextAreaElement | null>(null);
  const [hovered, setHovered] = useState(false);

  const onSend = () => {
    setIsEditing(false);
    deleteLogsAfterMutation(environment, sessionId, notify, message.id, {
      edit,
    });
  };

  if (editing) {
    return (
      <Stack
        direction="column"
        sx={{ position: "relative", paddingTop: 1 }}
        gap={1}
      >
        <textarea
          className="aui-text-input"
          ref={inputFieldRef}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              onSend();
            } else if (e.key === "Escape") {
              setIsEditing(false);
            }
          }}
          autoFocus={true}
          value={edit}
          onChange={(e) => setEdit(e.target.value)}
        />
        <Stack direction="row" justifyContent="flex-end" gap={1}>
          <Typography
            variant="subtitle2"
            component="div"
            sx={{ marginRight: "auto" }}
          >
            All the logs and messages after the edited message will be dropped.
          </Typography>
          <Button onClick={() => setIsEditing(false)}>Cancel</Button>
          <Button
            disabled={edit === message.content || edit === ""}
            onClick={onSend}
          >
            Send
          </Button>
        </Stack>
      </Stack>
    );
  }

  return (
    <Stack
      direction="row"
      sx={{
        display: "flex",
        width: "fit-content",
        maxWidth: "66%",
        marginLeft: "auto",
        justifyContent: "flex-end",
      }}
    >
      <Stack
        onMouseOver={() => setHovered(true)}
        onMouseOut={() => setHovered(false)}
        sx={{
          display: "flex",
          alignItems: "flex-end",
        }}
      >
        {Array.isArray(message.attachments) &&
          message.attachments.length > 0 && (
            <Stack
              justifyContent={"right"}
              sx={{
                maxWidth: "100%",
                display: "flex",
                flexWrap: "wrap",
                marginBottom: 1,
                marginRight: 4,
              }}
              direction="row"
              gap={1}
            >
              {message.attachments.map((attachment, index) => {
                return <Attachment key={index} attachment={attachment} />;
              })}
            </Stack>
          )}
        <Stack direction="row" alignItems="center" gap={1}>
          <motion.div
            initial={isPending ? { opacity: 0, scale: 0 } : false}
            animate={{ opacity: 1, scale: 1, transformOrigin: "right bottom" }}
            transition={{ type: "tween", duration: 0.2 }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "flex-end",
                width: "fit-content",
                maxWidth: "100%",
                paddingTop: 1.5,
                paddingBottom: 1.5,
                paddingLeft: 1.5,
                paddingRight: 1.5,
                borderRadius: 2,
                backgroundColor: "#2C2D30",
                fontSize: "14px",
                lineHeight: "17px",
                border: "1px solid ##FFFFFF1A",
                marginTop: 1,
                marginBottom: 1,
                position: "relative",
                zIndex: 1,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {formatMessage(message)}
            </Box>
          </motion.div>
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              width: "30px",
              color: alpha(theme.palette.text.secondary, 0.8),
            }}
          >
            {isPending ? (
              <CircularProgress
                size={"1rem"}
                color="inherit"
                sx={{ display: "flex" }}
              />
            ) : (
              <IconButton
                size="small"
                sx={{
                  visibility: hovered ? "visible" : "hidden",
                }}
                onClick={() => {
                  setIsEditing(true);
                  setTimeout(() => {
                    inputFieldRef.current?.focus();
                  }, 0);
                }}
              >
                <EditIcon fontSize="inherit" />
              </IconButton>
            )}
          </Box>
        </Stack>
        <Stack
          direction={"row"}
          gap={1}
          sx={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            marginRight: 5,
          }}
        >
          {showTimestamps && (
            <Box
              sx={{
                color: alpha(theme.palette.text.secondary, 0.8),
                fontSize: "12px",
              }}
            >
              {formatDateAndTimeFromTime(message.timestamp * 1000)}
            </Box>
          )}
        </Stack>
      </Stack>
    </Stack>
  );
}

function Attachment({ attachment }: { attachment: string }) {
  const { filesystemPath } = useAppContext();

  if (filesystemPath == null) {
    return null;
  }

  if (IMAGE_EXTENSION_REGEX.test(attachment)) {
    return (
      <ImageAttachment
        attachment={attachment}
        filesystemPath={filesystemPath}
      />
    );
  } else {
    return (
      <FileAttachment attachment={attachment} filesystemPath={filesystemPath} />
    );
  }
}

function ImageAttachment({
  attachment,
  filesystemPath,
}: {
  attachment: string;
  filesystemPath: string;
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const image = normalizePath(attachment, filesystemPath);
  const sessionRoot = getSessionRoot(filesystemPath ?? "");
  const displayPath = image?.split(sessionRoot).slice(-1).pop();

  return (
    <>
      <motion.div
        initial={{ borderRadius: 8 }}
        animate={{
          width: loading ? 100 : "auto",
          height: loading ? 100 : "auto",
          minWidth: loading ? 20 : 1,
          minHeight: loading ? 20 : 1,
        }}
        transition={{
          type: "tween",
        }}
        style={{
          position: "relative",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          borderRadius: "8px",
          border: "1px solid #FFFFFF1A",
          margin: "1px",
          backgroundColor: "#25272c",
          overflow: "hidden",
        }}
      >
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                position: "absolute",
                zIndex: 1,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                width: "100%",
                height: "100%",
              }}
            >
              <CircularProgress size={40} />
            </motion.div>
          )}
        </AnimatePresence>
        <motion.img
          onClick={() => setOpen(true)}
          initial={{ opacity: 0 }}
          animate={{ opacity: loading ? 0 : 1 }}
          transition={{
            opacity: { duration: 0.3 },
          }}
          style={{
            maxWidth: "200px",
            maxHeight: "150px",
            flex: 1,
            borderRadius: "8px",
            objectFit: "cover",
            cursor: "pointer",
          }}
          src={image}
          onLoad={() => setLoading(false)}
        />
      </motion.div>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        style={{ maxHeight: "100%" }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginLeft: 2,
          }}
        >
          <Typography variant="caption" component="div">
            <b>Attachment:</b> {displayPath}
          </Typography>
          <IconButton onClick={() => setOpen(false)}>
            <CloseOutlinedIcon />
          </IconButton>
        </Box>
        <img src={image} style={{ width: "100%" }} />
      </Dialog>
    </>
  );
}

function FileAttachment({
  attachment,
  filesystemPath,
}: {
  attachment: string;
  filesystemPath: string;
}) {
  const file = normalizePath(attachment, filesystemPath);

  return (
    <Chip
      href={file}
      clickable
      component="a"
      target="_blank"
      icon={<AttachFileIcon />}
      label={file.split("/").pop()}
    />
  );
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import {
  alpha,
  Box,
  Chip,
  IconButton,
  InputBase,
  Paper,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { AnimatePresence, motion } from "motion/react";
import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRelayEnvironment } from "react-relay";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import { usePendingMessages } from "../../contexts/PendingMessagesContext";
import SessionIdContext from "../../contexts/SessionIdContext";
import { useInteractiveScenarioDialogTree } from "../../hooks/useInteractiveScenario";
import { commitPlayAsync } from "../../mutations/PlayMutation";
import commitSendUserMessageToAgent, {
  Attachment,
} from "../../mutations/SendUserMessageToAgentMutation";
import {
  validateFileAttachment,
  validateFileType,
  validateTotalSize,
} from "../../utils/fileUtils";
import { AGENT_USER_INTERFACE_APP_NAME, EnvState } from "../../utils/types";
import FileInput, { FileInputHandle } from "../common/inputs/FileInput";
import { EnvironmentControlButton } from "./EnvironmentControlButton";
import { InfoLevelMenu } from "./InfoLevelMenu";
import { SUPPORTED_IMAGE_FORMATS } from "./constants";

const IMAGE_EXTENSIONS = SUPPORTED_IMAGE_FORMATS.map((ext) => `.${ext}`).join(
  ",",
);

export function ChatInput() {
  const { appsState, scenario, eventLog, envState, localEnvState } =
    useAppContext();
  const inputBaseRef = useRef<HTMLInputElement | null>(null);
  const fileInputRef = useRef<FileInputHandle>(null);
  const [inputData, setInputData] = useState<string | null>(null);
  const [isFocused, setIsFocused] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isDialogOptionProcessing, setIsDialogOptionProcessing] =
    useState(false);
  const isStopped = envState === EnvState.STOPPED;
  const isFailed = envState === EnvState.FAILED;
  const environment = useRelayEnvironment();
  const sessionId = useContext(SessionIdContext);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const { notify } = useNotifications();
  const theme = useTheme();
  let fileInputAccept = IMAGE_EXTENSIONS;
  let fileAttachmentTooltip = "Attach image";

  // Shared function to handle file uploads
  const handleFileUpload = (file: File) => {
    // Validate individual file
    const fileValidation = validateFileAttachment(file);
    if (!fileValidation.isValid) {
      notify({
        message: fileValidation.error || "File validation failed",
        type: "error",
      });
      return;
    }

    // Validate total size including this new file
    const allFiles = [...attachments.map((a) => a.file), file];
    const totalValidation = validateTotalSize(allFiles);
    if (!totalValidation.isValid) {
      notify({
        message: totalValidation.error || "Total size validation failed",
        type: "error",
      });
      return;
    }

    // Check if file is already in attachments
    if (
      attachments.some(
        (attachment) =>
          attachment.file.name === file.name &&
          attachment.file.size === file.size,
      )
    ) {
      // File already exists, no-op
      return;
    }

    // File passed validation, proceed with upload
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result?.toString();
      if (base64 != null) {
        setAttachments((prev) => [
          ...prev,
          {
            file,
            base64: base64.split(",")[1],
          },
        ]);
      }
    };
    reader.readAsDataURL(file);
  };

  // Extract user messages for interactive scenario logic
  const userMessages = eventLog
    .filter(
      (evt) =>
        evt.event_type === "USER" &&
        evt.action != null &&
        evt.action.app_name === AGENT_USER_INTERFACE_APP_NAME &&
        evt.action.function_name === "send_message_to_agent",
    )
    .map((userEvent) => userEvent.action.args.content)
    .filter((x) => x != null);

  // Use the custom hook to get the dialog tree for the current scenario
  const dialogTree = useInteractiveScenarioDialogTree(
    scenario?.scenarioId,
    userMessages,
  );

  // Get the pending messages context
  const { addPendingMessage, removePendingMessage } = usePendingMessages();

  // Local state to track pending messages for cleanup
  const [localPendingMessages, setLocalPendingMessages] = useState<
    Map<string, string | null>
  >(new Map()); // Map of pendingId -> correlationId

  // Effect to clean up pending messages that have been processed
  useEffect(() => {
    // Check if any pending messages have been processed
    const pendingMessageEntries = Array.from(localPendingMessages.entries());

    for (const [pendingId, correlationId] of pendingMessageEntries) {
      if (!correlationId) continue; // Skip messages that don't have a correlation key yet

      // Check if this message's correlation key exists in the event log
      const messageExists = eventLog.some(
        (event) => event.metadata?.return_value === correlationId,
      );

      if (messageExists) {
        // Remove from local pending messages
        setLocalPendingMessages((prev) => {
          const newMap = new Map(prev);
          newMap.delete(pendingId);
          return newMap;
        });

        // Also remove from the context
        removePendingMessage(pendingId);
      }
    }
  }, [eventLog, localPendingMessages, removePendingMessage]);

  const onSendRequest = useCallback(
    async (query: string | null, attachments: Array<Attachment>) => {
      if (query === null || query.trim() === "" || isStopped) {
        return;
      }

      // Set processing state to true to prevent multiple clicks
      setIsDialogOptionProcessing(true);

      // Create a temporary ID for the pending message
      const pendingId = `pending-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      // Track locally for cleanup with null correlationId initially
      setLocalPendingMessages((prev) => {
        const newMap = new Map(prev);
        newMap.set(pendingId, null);
        return newMap;
      });

      // Add pending message to context for display
      addPendingMessage({
        id: pendingId,
        content: query,
        attachments: attachments.map((a) => a.file.name),
        timestamp: Date.now() / 1000, // Convert to seconds to match backend timestamp format
        correlationId: null, // Initially null, will be updated when we get the real message ID
      });

      setInputData(null);
      setAttachments([]);
      setSelectedFile(null);

      // Some setup happens when environment starts e.g. setting the right time that we need to do before the first message.
      if (envState === EnvState.SETUP) {
        await commitPlayAsync(environment, sessionId, notify);
      }

      commitSendUserMessageToAgent(
        environment,
        query,
        attachments,
        sessionId,
        notify,
        (messageId) => {
          // When we get the real message ID from the backend, remove the pending message
          // and add a new one with the correlation key
          removePendingMessage(pendingId);

          // Add a new pending message with the real message ID as the correlation key
          addPendingMessage({
            id: pendingId,
            content: query,
            attachments: attachments.map((a) => a.file.name),
            timestamp: Date.now() / 1000,
            correlationId: messageId,
          });

          // Also update our local tracking
          setLocalPendingMessages((prev) => {
            const newMap = new Map(prev);
            newMap.set(pendingId, messageId);
            return newMap;
          });
        },
        () => {
          // Handle error - remove pending message and reset processing state
          removePendingMessage(pendingId);
          setLocalPendingMessages((prev) => {
            const newMap = new Map(prev);
            newMap.delete(pendingId);
            return newMap;
          });
          setIsDialogOptionProcessing(false);
        },
      );
    },
    [
      setAttachments,
      setSelectedFile,
      addPendingMessage,
      removePendingMessage,
      environment,
      sessionId,
      notify,
      envState,
      isStopped,
    ],
  );

  const onInputEnter = (
    e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const target = e.target as HTMLTextAreaElement;
    if (
      e.key === "Enter" &&
      !e.shiftKey &&
      target.value &&
      target.value.trim() !== "" &&
      !isStopped
    ) {
      onSendRequest(inputData, attachments);
      e.preventDefault();
    }
  };

  const onInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputData(e.target.value);
  };

  // Check if suggestions should be shown:
  // - Show when there are no AgentUserInterface messages (initial state)
  // - Show when the last AgentUserInterface message is from the agent (not from user)
  const shouldShowSuggestions = useMemo(() => {
    // Iterate from the end to find the most recent AgentUserInterface message
    for (let i = eventLog.length - 1; i >= 0; i--) {
      const evt = eventLog[i];

      if (
        evt.action != null &&
        evt.action.app_name === AGENT_USER_INTERFACE_APP_NAME
      ) {
        // Found the last AgentUserInterface message from the agent
        const isFromAgent =
          evt.event_type === "AGENT" &&
          evt.action.function_name === "send_message_to_user";

        return isFromAgent;
      }
    }

    // No AgentUserInterface messages found - show suggestions (initial state)
    return true;
  }, [eventLog]);

  const dialogOptions = useMemo(
    () =>
      dialogTree != null &&
      Object.keys(dialogTree).length > 0 &&
      !isStopped &&
      !isDialogOptionProcessing &&
      shouldShowSuggestions && (
        <Stack gap={1}>
          <motion.div key="dialog-options-header">
            <Typography
              variant="subtitle2"
              color="textDisabled"
              sx={{ paddingX: 5 }}
            >
              Suggested prompts
            </Typography>
          </motion.div>
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 1,
              paddingX: 5,
              maxWidth: 500,
            }}
          >
            {Object.keys(dialogTree).map((dialogOption, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0 }}
                animate={{
                  opacity: 1,
                }}
              >
                <Chip
                  label={dialogOption}
                  onClick={() => {
                    onSendRequest(dialogOption, []);
                  }}
                  sx={{
                    paddingY: 1,
                    height: "100%",
                    display: "flex",
                    flexDirection: "row",
                    "& .MuiChip-label": {
                      overflowWrap: "break-word",
                      whiteSpace: "normal",
                      textOverflow: "clip",
                    },
                  }}
                />
              </motion.div>
            ))}
          </Box>
        </Stack>
      ),
    [
      dialogTree,
      isDialogOptionProcessing,
      isStopped,
      onSendRequest,
      shouldShowSuggestions,
    ],
  );

  useEffect(() => {
    setIsDialogOptionProcessing(false);
  }, [dialogTree]);

  const attachmentsChips = attachments.length > 0 && (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 1,
      }}
    >
      {attachments.map((attachment) => (
        <motion.div
          key={attachment.file.name}
          initial={{ opacity: 0 }}
          animate={{
            opacity: 1,
          }}
        >
          <Chip
            label={attachment.file.name}
            variant="outlined"
            onDelete={() =>
              setAttachments((prev) => prev.filter((a) => a !== attachment))
            }
          />
        </motion.div>
      ))}
    </Box>
  );

  const attachmentsDisabled =
    appsState.find((app) =>
      ["Files", "SandboxLocalFileSystem"].includes(app.app_name),
    ) === undefined;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2.5,
        alignItems: "flex-start",
        paddingBottom: 3,
        width: "100%",
      }}
    >
      <AnimatePresence>{dialogOptions}</AnimatePresence>
      <Paper
        component="form"
        elevation={2}
        sx={{
          width: "100%",
          bgcolor: theme.palette.background.default,
          padding: 1.5,
          cursor: "text",
          borderRadius: 4,
          border: `1px solid ${
            isDragging
              ? theme.palette.primary.main
              : isFocused
                ? alpha(theme.palette.action.focus, 0.2)
                : alpha(theme.palette.action.disabled, 0.05)
          }`,
          transition: "all 0.2s",
          backgroundColor: isDragging
            ? alpha(theme.palette.action.hover, 0.1)
            : "transparent",
        }}
        onClick={() => {
          inputBaseRef.current?.focus();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!attachmentsDisabled && !isStopped && !isFailed) {
            setIsDragging(true);
          }
        }}
        onDragLeave={() => {
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);

          if (attachmentsDisabled || isStopped || isFailed) {
            return;
          }

          const file = e.dataTransfer.files?.[0];
          if (file) {
            const isSupported = validateFileType(file);
            if (!isSupported) {
              notify({
                message: `File type not supported: ${file.name}`,
                type: "error",
              });
              return;
            }
            handleFileUpload(file);
          }
        }}
      >
        <Stack spacing={1}>
          <AnimatePresence>{attachmentsChips}</AnimatePresence>
          <InputBase
            multiline
            value={inputData ?? ""}
            placeholder={isStopped ? "Agent is stopped" : "Message agent"}
            onChange={onInputChange}
            onKeyDown={(e) => onInputEnter(e)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            autoFocus={true}
            disabled={isStopped || isFailed}
            maxRows={12}
            sx={{
              width: "100%",
            }}
            inputRef={inputBaseRef}
          />
          <Stack width="100%">
            <Box sx={{ display: "none" }}>
              <FileInput
                ref={fileInputRef}
                onFileSelected={(file) => {
                  if (file) {
                    handleFileUpload(file);
                  }
                }}
                accept={fileInputAccept}
                selectedFile={selectedFile}
              />
            </Box>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                width: "100%",
              }}
            >
              <Stack
                direction="row"
                spacing={0.5}
                alignItems="center"
                width="100%"
              >
                <Box>
                  <Tooltip
                    title={
                      attachmentsDisabled
                        ? "Files or SandboxLocalFileSystem app is required for using attachments"
                        : fileAttachmentTooltip
                    }
                  >
                    <span>
                      <IconButton
                        size="small"
                        onClick={() => {
                          fileInputRef.current?.openFileDialog();
                        }}
                        color="lightgrey"
                        sx={{ border: `1px solid ${theme.palette.divider}` }}
                        // Disable Attachments for VirtualFileSystem as they don't work as expected in read-only setup.
                        disabled={attachmentsDisabled || isStopped || isFailed}
                      >
                        <AttachFileIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                </Box>
                <InfoLevelMenu
                  anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "center",
                  }}
                  transformOrigin={{
                    vertical: "bottom",
                    horizontal: "center",
                  }}
                />
              </Stack>
              <Stack
                direction="row"
                alignItems="center"
                width="100%"
                justifyContent="flex-end"
                spacing={0.5}
              >
                {!localEnvState ||
                ((localEnvState === EnvState.SETUP ||
                  envState === EnvState.SETUP) &&
                  eventLog.length === 0) ||
                inputData ? (
                  <Tooltip title="Send message">
                    <span>
                      <IconButton
                        size="small"
                        sx={{
                          color: theme.palette.primary.contrastText,
                          bgcolor: theme.palette.secondary.main,
                          "&:hover": {
                            bgcolor: theme.palette.secondary.dark,
                          },
                          "&.Mui-disabled": {
                            bgcolor: theme.palette.secondary.main,
                            color: theme.palette.primary.contrastText,
                            opacity: 0.3,
                          },
                          transition: "opacity 0.2s",
                        }}
                        color="inherit"
                        onClick={() => onSendRequest(inputData, attachments)}
                        disabled={
                          !inputData ||
                          inputData.trim() === "" ||
                          isStopped ||
                          isFailed
                        }
                      >
                        <ArrowUpwardIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                ) : (
                  <EnvironmentControlButton />
                )}
              </Stack>
            </Box>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
}

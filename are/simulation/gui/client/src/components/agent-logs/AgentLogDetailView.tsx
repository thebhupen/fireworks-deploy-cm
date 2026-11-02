// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import EditIcon from "@mui/icons-material/Edit";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useContext, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import EnvStateContext from "../../contexts/EnvStateContext";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../contexts/SessionIdContext";
import commitAmendAndReplay from "../../mutations/AmendAndReplayMutation";
import useRelayEnvironment from "../../relay/RelayEnvironment";
import { maybeUserDevServerPath } from "../../utils/PathUtils";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import { AgentLog, EnvState, isEditableLog } from "../../utils/types";
import CopyToClipboard from "../common/CopyToClipboard";
import ExpandableSection from "../common/ExpandableSection";
import JSONView from "../JSONView";
import { TextPairing } from "../TextPairing";

export function AgentLogDetailView({ log }: { log: AgentLog | void }) {
  const theme = useTheme();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const stringValue = useMemo(() => JSON.stringify(log, null, 2), [log]);
  const [rawContentExpanded, setRawContentExpanded] = useState(true);
  const [formattedContentExpanded, setFormattedContentExpanded] =
    useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [displayContent, setDisplayContent] = useState("");
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);

  const sessionId = useContext(SessionIdContext);
  const envState = useContext(EnvStateContext);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();
  const isRunning = envState === EnvState.RUNNING;

  const isMarkdown = (text: string): boolean => {
    const markdownPatterns = [
      /^#+ /, // Headers
      /\*\*.+\*\*/, // Bold
      /\*.+\*/, // Italic
      /\[.+\]\(.+\)/, // Links
      /```[\s\S]*```/, // Code blocks
      /^\s*[-*+] /, // Lists
      /^\s*\d+\. /, // Numbered lists
    ];

    return markdownPatterns.some((pattern) => pattern.test(text));
  };

  const isValidJSON = (text: string): boolean => {
    if (text === "" || text === "None") {
      return false;
    }
    try {
      JSON.parse(text);
      return true;
    } catch (e) {
      return false;
    }
  };

  interface MessageItem {
    role: string;
    content: string;
    attachment: any[];
  }

  const isMessageListJSON = (text: string): boolean => {
    if (!isValidJSON(text)) return false;

    try {
      const parsed = JSON.parse(text);
      if (!Array.isArray(parsed)) return false;

      // Check if all items have the expected structure
      return parsed.every(
        (item) =>
          typeof item === "object" &&
          item !== null &&
          typeof item.role === "string" &&
          typeof item.content === "string",
      );
    } catch (e) {
      return false;
    }
  };

  const hasFormattedContent = useMemo(() => {
    if (!log?.content) return false;
    return isValidJSON(log.content) || isMarkdown(log.content);
  }, [log?.content]);

  const isEditable = useMemo(() => {
    return isEditableLog(log);
  }, [log]);

  useEffect(() => {
    setFormattedContentExpanded(true);
    setRawContentExpanded(true);
    setIsEditing(false);
    if (log?.content) {
      setEditedContent(log.content);
      setDisplayContent(log.content);
    }

    // Scroll to the top when a new log is selected
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [log, hasFormattedContent]);

  const handleConfirmSave = () => {
    setConfirmDialogOpen(false);
    handleSaveContent();
  };

  const handleSaveContent = async () => {
    try {
      if (!log?.id) {
        console.error("No log ID found");
        return;
      }

      commitAmendAndReplay(
        environment,
        sessionId,
        log?.id,
        editedContent,
        notify,
      );

      setIsEditing(false);

      notify({
        message: `Successfully replayed logs from ${log.id}.`,
        type: "success",
      });
    } catch (error) {
      console.error("Error saving content:", error);
    }
  };

  const renderHeader = () => (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="space-between"
      padding={theme.spacing(1.5)}
      sx={{
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
      {log != null && (
        <Stack direction="row" alignItems="center" spacing={1}>
          <Typography variant="h6" fontWeight="bold">
            {log.type}
          </Typography>
          {isEditable && !isEditing && (
            <Tooltip
              title={
                isRunning
                  ? "Agent must be stopped before editing logs"
                  : "Edit log"
              }
              arrow
            >
              <span>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setIsEditing(true)}
                  startIcon={<EditIcon />}
                  disabled={isRunning}
                >
                  Edit
                </Button>
              </span>
            </Tooltip>
          )}
        </Stack>
      )}
      {log != null && (
        <CopyToClipboard label="Copy log as JSON" value={stringValue} />
      )}
    </Stack>
  );

  const renderBasicInfo = () => (
    <>
      {log?.id && <TextPairing heading="ID" description={log?.id} />}
      {log?.timestamp && (
        <TextPairing
          heading="Timestamp"
          description={formatDateAndTimeFromTime(log.timestamp * 1000)}
        />
      )}
    </>
  );

  const renderFormattedContent = () => {
    if (!log?.content) {
      return null;
    }

    if (isMessageListJSON(displayContent)) {
      const messages = JSON.parse(displayContent) as MessageItem[];
      return (
        <ExpandableSection
          title="Messages"
          isExpanded={formattedContentExpanded}
          setExpanded={setFormattedContentExpanded}
        >
          <Stack spacing={2}>
            {messages.map((message: MessageItem, index: number) => (
              <Box
                key={index}
                sx={{
                  backgroundColor: theme.palette.action.hover,
                  borderRadius: 1,
                  padding: theme.spacing(2),
                  boxShadow: 1,
                }}
              >
                <Box
                  sx={{
                    display: "inline-block",
                    backgroundColor: theme.palette.primary.main,
                    color: theme.palette.primary.contrastText,
                    borderRadius: "16px",
                    padding: "4px 12px",
                    fontSize: "0.875rem",
                    fontWeight: "bold",
                    mb: 1,
                  }}
                >
                  {message.role}
                </Box>
                <Box
                  sx={{
                    fontFamily: "monospace",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    pl: 1,
                    mt: 1,
                  }}
                >
                  {message.content.trim()}
                </Box>
              </Box>
            ))}
          </Stack>
        </ExpandableSection>
      );
    } else if (isValidJSON(displayContent)) {
      return (
        <ExpandableSection
          title="JSON"
          isExpanded={formattedContentExpanded}
          setExpanded={setFormattedContentExpanded}
        >
          <Box
            sx={{
              backgroundColor: theme.palette.action.hover,
              padding: theme.spacing(2),
              borderRadius: 1,
            }}
          >
            <JSONView json={JSON.parse(displayContent)} longTextWrap={true} />
          </Box>
        </ExpandableSection>
      );
    } else if (isMarkdown(displayContent)) {
      return (
        <ExpandableSection
          title="Markdown"
          isExpanded={formattedContentExpanded}
          setExpanded={setFormattedContentExpanded}
        >
          <Box
            sx={{
              backgroundColor: theme.palette.action.hover,
              padding: theme.spacing(2),
              borderRadius: 1,
            }}
          >
            <ReactMarkdown
              components={{
                code: ({ node, className, children, ...props }) => (
                  <code
                    className={className}
                    style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
                    {...props}
                  >
                    {children}
                  </code>
                ),
              }}
            >
              {displayContent}
            </ReactMarkdown>
          </Box>
        </ExpandableSection>
      );
    } else if (log.content !== "None") {
      // The ActionExecutor currently outputs Python print statements instead of proper JSON
      // This is a temporary workaround to convert that output to valid JSON format
      try {
        const processedContent = log.content
          .replace(/'/g, '"')
          .replace(/None/g, "null")
          .replace(/True/g, "true")
          .replace(/False/g, "false");

        const parsedJson = JSON.parse(processedContent);

        return (
          <ExpandableSection
            title="JSON"
            isExpanded={formattedContentExpanded}
            setExpanded={setFormattedContentExpanded}
          >
            <Box
              sx={{
                backgroundColor: theme.palette.action.hover,
                padding: theme.spacing(2),
                borderRadius: 1,
              }}
            >
              <JSONView json={parsedJson} longTextWrap={true} />
            </Box>
          </ExpandableSection>
        );
      } catch (e) {}
    }
    return null;
  };

  const renderAttachments = () => {
    if (!log?.type || !["TASK", "OBSERVATION"].includes(log.type)) {
      return null;
    }

    return (
      <ExpandableSection
        title="Attachments"
        isExpanded={true}
        setExpanded={() => {}}
      >
        {!log?.attachments || log.attachments.length === 0 ? (
          <Typography>No attachments</Typography>
        ) : (
          log.attachments.map((attachment, index) => (
            <Box
              key={index}
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: theme.spacing(2),
                backgroundColor: theme.palette.action.hover,
                padding: theme.spacing(2),
                borderRadius: 1,
                marginBottom: theme.spacing(2),
              }}
            >
              <Typography>{`Attachment: ${index + 1}, Type: ${attachment.mime}, Length: ${attachment.length} bytes`}</Typography>
              {(() => {
                const attachmentUrl = maybeUserDevServerPath(attachment.url);
                if (attachment.mime.startsWith("image/")) {
                  return (
                    <a
                      href={attachmentUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <img
                        src={attachmentUrl}
                        alt={`Attachment ${index}`}
                        style={{
                          maxWidth: "600px",
                          maxHeight: "600px",
                          cursor: "pointer",
                        }}
                      />
                    </a>
                  );
                } else {
                  return (
                    <Button
                      color="primary"
                      component="a"
                      href={attachmentUrl}
                      download
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{ mt: 1, maxWidth: "fit-content" }}
                    >
                      Download
                    </Button>
                  );
                }
              })()}
            </Box>
          ))
        )}
      </ExpandableSection>
    );
  };

  const renderRawContent = () => {
    if (!log?.content) return null;

    return (
      <ExpandableSection
        title="Raw"
        isExpanded={rawContentExpanded}
        setExpanded={setRawContentExpanded}
      >
        <Box
          sx={{
            backgroundColor: theme.palette.action.hover,
            padding: theme.spacing(2),
            borderRadius: 1,
            fontFamily: "monospace",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {displayContent}
        </Box>
      </ExpandableSection>
    );
  };

  const renderErrorDetails = () => {
    if (!log?.type || !["ERROR"].includes(log.type)) {
      return null;
    }

    return (
      <ExpandableSection
        title="Error Details"
        isExpanded={true}
        setExpanded={() => {}}
      >
        <>
          <Stack mt={theme.spacing(2)}>
            <Typography fontWeight="bold">Exception</Typography>
            <Box
              sx={{
                backgroundColor: theme.palette.action.hover,
                padding: theme.spacing(2),
                borderRadius: 1,
                fontFamily: "monospace",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {log.exception ?? "Unknown"}
            </Box>
          </Stack>

          <Stack mt={theme.spacing(2)}>
            <Typography fontWeight="bold">Stack Trace</Typography>
            <Box
              sx={{
                backgroundColor: theme.palette.action.hover,
                padding: theme.spacing(2),
                borderRadius: 1,
                fontFamily: "monospace",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {log.exceptionStackTrace ?? "Unknown"}
            </Box>
          </Stack>
        </>
      </ExpandableSection>
    );
  };

  const renderEditingView = () => {
    if (!log?.content) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <TextField
          fullWidth
          multiline
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          slotProps={{
            input: {
              sx: {
                fontFamily: "monospace",
                backgroundColor: theme.palette.action.hover,
                whiteSpace: "pre-wrap",
                height: "auto",
              },
            },
          }}
        />
        <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => setConfirmDialogOpen(true)}
            sx={{ mr: 1 }}
          >
            Save
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              setIsEditing(false);
              setEditedContent(log.content ?? "");
              setDisplayContent(log.content ?? "");
            }}
          >
            Cancel
          </Button>
        </Box>
      </Box>
    );
  };

  return (
    <Paper
      elevation={5}
      sx={{ borderRadius: 2, width: "100%", overflowY: "auto" }}
    >
      <Stack flexGrow={1}>
        {renderHeader()}
        <Stack
          padding={theme.spacing(2)}
          gap={theme.spacing(3)}
          sx={{
            overflow: "auto",
          }}
          ref={scrollContainerRef}
        >
          {renderBasicInfo()}
          {isEditing ? (
            renderEditingView()
          ) : (
            <>
              {renderAttachments()}
              {log?.content && renderFormattedContent()}
              {renderErrorDetails()}
              {log?.content && renderRawContent()}
            </>
          )}
        </Stack>
      </Stack>

      <Dialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">Confirm Save</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            All subsequent logs will be dropped/replaced with the new ones. Are
            you sure you want to continue?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmSave}
            color="primary"
            variant="contained"
            autoFocus
          >
            Continue
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

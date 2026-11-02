// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CodeIcon from "@mui/icons-material/Code";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import {
  alpha,
  Avatar,
  Box,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Divider,
  Drawer,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import { useAppContext } from "../../../../contexts/AppContextProvider.js";
import useCopyToClipboard from "../../../../hooks/useCopyToClipboard.js";
import { formatDateAndTimeFromTime } from "../../../../utils/TimeUtils.js";
import { AppName, LogEvent } from "../../../../utils/types.js";
import { EVENT_NODE_CONFIG } from "../../../dag/EventNode.js";
import JSONView, { JSONType } from "../../../JSONView.js";
import { CARD_WIDTH, CONNECTOR_HEIGHT, getIcon } from "./TimelineConstants.js";

interface TimelineItemProps {
  event: LogEvent;
}

/**
 * Timeline item component for displaying events in the timeline
 */
const TimelineItem = ({ event }: TimelineItemProps) => {
  const theme = useTheme();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { isCopied: isEventIdCopied, handleCopy: handleCopyEventId } =
    useCopyToClipboard(event.event_id);

  const action = event?.action;
  const config =
    EVENT_NODE_CONFIG[event.event_type] ?? EVENT_NODE_CONFIG.DEFAULT;
  const palette = useMemo(
    () => theme.palette.augmentColor({ color: { main: config.color } }),
    [theme, config],
  );
  const scheduled = event.event_time !== undefined && event.event_time !== null;

  const timeLabel = scheduled
    ? formatDateAndTimeFromTime(event.event_time! * 1000)
    : `(+${event.event_relative_time ?? 0} s)`;

  const { userPreferences } = useAppContext();
  const [showExpandedArgs, setShowExpandedArgs] = useState(
    userPreferences.annotator.enhanceReadability,
  );

  // Update showExpandedArgs when enhanceReadability preference changes
  useEffect(() => {
    setShowExpandedArgs(userPreferences.annotator.enhanceReadability);
  }, [userPreferences.annotator.enhanceReadability]);

  const args = useMemo(() => {
    const resolvedArgs = action?.resolved_args;
    const argsToUse =
      resolvedArgs && Object.keys(resolvedArgs).length > 0
        ? resolvedArgs
        : action?.args;
    return argsToUse
      ? Object.entries(argsToUse).map(([key, value]) => (
          <>
            <Typography color="textSecondary" key={key}>
              {key}
            </Typography>
            <Typography key={`${key}-value`}>
              {typeof value === "object"
                ? JSON.stringify(value)
                : String(value)}
            </Typography>
          </>
        ))
      : [];
  }, [action]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          width: "100%",
        }}
      >
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: CONNECTOR_HEIGHT }}
          transition={{ duration: 0.3 }}
        >
          <Box
            sx={{
              width: 2,
              height: "100%",
              bgcolor: theme.palette.text.disabled,
            }}
          />
        </motion.div>
        <Card
          elevation={3}
          sx={{
            border: event.metadata.exception
              ? `1px solid ${theme.palette.error.main}`
              : "none",
            cursor: "pointer",
            width: CARD_WIDTH,
            bgcolor: alpha(theme.palette.background.paper, 0.5),
            "&:hover": {
              boxShadow: theme.shadows[6],
              bgcolor: alpha(theme.palette.background.paper, 0.3),
            },
            position: "relative",
            overflow: "visible",
          }}
          onClick={() => setShowExpandedArgs((prev) => !prev)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <CardContent>
            <Stack spacing={1}>
              <Box
                justifyContent={"space-between"}
                alignItems={"center"}
                display="flex"
              >
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Avatar
                    sx={{
                      bgcolor: palette.dark,
                      color: "#FFFFFF",
                      height: 24,
                      width: 24,
                    }}
                    variant="rounded"
                  >
                    {getIcon(
                      event.event_type,
                      action?.app_name
                        ? (action.app_name as AppName)
                        : undefined,
                    )}
                  </Avatar>
                  <Typography
                    variant="subtitle1"
                    color={palette.light}
                    fontWeight="bold"
                  >
                    {config.label}
                  </Typography>
                </Stack>
                <Typography color="textSecondary">
                  {timeLabel}
                  {!scheduled && " (NOT SCHEDULED)"}
                </Typography>
              </Box>
              {action && (
                <Typography
                  noWrap
                  sx={{ fontFamily: "monospace", fontWeight: "bold", pl: 0.5 }}
                >
                  {action.app_name === "AgentUserInterface"
                    ? ""
                    : `${action.app_name}.`}
                  {action.function_name}
                </Typography>
              )}
              {args.length > 0 && (
                <Box>
                  <div
                    style={{
                      borderRadius: theme.shape.borderRadius,
                      padding: "4px",
                      wordBreak: "break-word",
                      fontFamily: "monospace",
                      cursor: "pointer",
                      position: "relative",
                    }}
                  >
                    <div
                      style={{
                        display: showExpandedArgs ? "none" : "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        minHeight: "3lh",
                      }}
                    >
                      {args}
                    </div>
                    <div
                      style={{
                        display: showExpandedArgs ? "block" : "none",
                      }}
                    >
                      {args.map((arg, index) => (
                        <Stack spacing={1} key={index}>
                          {index > 0 && <Divider sx={{ paddingTop: 1 }} />}
                          {arg}
                        </Stack>
                      ))}
                    </div>
                  </div>
                </Box>
              )}
              {event.metadata.exception && (
                <Stack direction={"row"} alignItems={"center"} spacing={1}>
                  <ErrorOutlineIcon
                    htmlColor={theme.palette.error.light}
                    fontSize="inherit"
                  />
                  <Typography
                    color={theme.palette.error.light}
                    sx={{
                      fontWeight: "bold",
                    }}
                  >
                    {event.metadata.exception}
                  </Typography>
                </Stack>
              )}
            </Stack>
          </CardContent>
          <Box
            sx={{
              position: "relative",
              height: "32px",
              width: "100%",
              mb: "-40px",
              zIndex: 1,
            }}
          >
            <AnimatePresence>
              {isHovered && (
                <motion.div
                  key={`${event.event_id}-controls`}
                  style={{
                    position: "absolute",
                    top: 0,
                    right: 0,
                    justifyContent: "right",
                    zIndex: 10,
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ButtonGroup
                    variant="text"
                    size="small"
                    color="lightgrey"
                    sx={{
                      backgroundColor: alpha(
                        theme.palette.background.default,
                        0.8,
                      ),
                    }}
                  >
                    <Tooltip title="Event Details">
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsDrawerOpen(true);
                        }}
                      >
                        <CodeIcon fontSize="small" />
                      </Button>
                    </Tooltip>
                    <Tooltip
                      title={isEventIdCopied ? "Copied!" : "Copy Event ID"}
                    >
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopyEventId();
                        }}
                      >
                        <ContentCopyIcon fontSize="small" />
                      </Button>
                    </Tooltip>
                  </ButtonGroup>
                </motion.div>
              )}
            </AnimatePresence>
          </Box>
        </Card>
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: CONNECTOR_HEIGHT }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Box
            sx={{
              width: 2,
              height: "100%",
              bgcolor: theme.palette.text.disabled,
            }}
          />
        </motion.div>

        <Drawer
          open={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          anchor="right"
        >
          <Stack spacing={2} sx={{ p: 3, width: "100%", maxWidth: "1000px" }}>
            <Typography variant="h6">
              Event Details: {event.event_type}
            </Typography>
            <Typography variant="subtitle2">{event.event_id}</Typography>
            <Card>
              <CardContent>
                <JSONView json={event as unknown as JSONType} />
              </CardContent>
            </Card>
          </Stack>
        </Drawer>
      </Box>
    </motion.div>
  );
};

export default TimelineItem;

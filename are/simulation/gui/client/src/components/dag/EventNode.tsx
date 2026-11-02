// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import AccessTimeIcon from "@mui/icons-material/AccessTime";
import CircleIcon from "@mui/icons-material/Circle";
import CodeIcon from "@mui/icons-material/Code";
import ForkRightIcon from "@mui/icons-material/ForkRight";
import PanToolIcon from "@mui/icons-material/PanTool";
import PersonIcon from "@mui/icons-material/Person";
import RuleIcon from "@mui/icons-material/Rule";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import {
  alpha,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { Handle, Position } from "@xyflow/react";
import { AnimatePresence, motion } from "motion/react";
import React, { memo, useContext, useEffect, useMemo, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import ScenarioExecutionContext from "../../contexts/ScenarioExecutionContext";
import useCopyToClipboard from "../../hooks/useCopyToClipboard";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import {
  AppName,
  ARESimulationEvent,
  ARESimulationEventType,
} from "../../utils/types";
import AppIcon from "../icons/AppIcon";
import "./dag.css";
import EventNodeControls from "./EventNodeControls";
import { useNodeSelection } from "./NodeSelectionContext";

type Props = {
  data: {
    event: ARESimulationEvent;
  };
};

interface EventNodeConfig {
  label: string;
  color: string;
}

export const EVENT_NODE_CONFIG: Record<string, EventNodeConfig> = {
  AGENT: {
    label: "Agent",
    color: "#C930C8",
  },
  ENV: {
    label: "Env",
    color: "#009688",
  },
  USER: {
    label: "User",
    color: "#00ABFF",
  },
  CONDITION: {
    label: "Condition",
    color: "#ff6a00",
  },
  VALIDATION: {
    label: "Validation",
    color: "#4CAF50",
  },
  STOP: {
    label: "Stop",
    color: "#EF5350",
  },
  DEFAULT: {
    label: "Default",
    color: "#888",
  },
};

const NODE_AVATAR_BACKGROUND_COLOR = "#46494A";
const NODE_BORDER_COLOR = "#8a8a8a";
const NODE_WIDTH = 400;
const TEXT_PADDING = "4px";
const EDITABLE_EVENT_TYPES = [
  ARESimulationEventType.User,
  ARESimulationEventType.Agent,
  ARESimulationEventType.Env,
];

const getIcon = (eventType: string, appName?: AppName) => {
  switch (eventType) {
    case ARESimulationEventType.Agent:
    case ARESimulationEventType.User:
    case ARESimulationEventType.Env:
      if (!appName) {
        return <CodeIcon />;
      }
      if (appName === "AgentUserInterface") {
        return eventType === ARESimulationEventType.Agent ? (
          <SmartToyIcon />
        ) : (
          <PersonIcon />
        );
      }
      return <AppIcon appName={appName} size={20} color="white" />;
    case ARESimulationEventType.Condition:
      return <ForkRightIcon />;
    case ARESimulationEventType.Validation:
      return <RuleIcon />;
    case ARESimulationEventType.Stop:
      return <PanToolIcon />;
    default:
      return <CircleIcon />;
  }
};

const EventNode = ({ data }: Props): React.ReactNode => {
  const { userPreferences } = useAppContext();
  const { selectNode, selectedNodeId, highlightedNodeId } = useNodeSelection();
  const event = data.event;
  const action = event?.action;
  const isEditable = useContext(ScenarioExecutionContext).isEditable;
  const showEditControls = EDITABLE_EVENT_TYPES.includes(event.event_type);
  const theme = useTheme();
  const isSelected = selectedNodeId === event.event_id;
  const isHighlighted = highlightedNodeId === event.event_id;
  const config =
    EVENT_NODE_CONFIG[event.event_type] ?? EVENT_NODE_CONFIG.DEFAULT;
  const [showExpandedArgs, setShowExpandedArgs] = useState(false);
  const { isCopied: isEventIdCopied, handleCopy: handleCopyEventId } =
    useCopyToClipboard(event.event_id);
  const palette = useMemo(
    () => theme.palette.augmentColor({ color: { main: config.color } }),
    [theme, config],
  );

  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (!isSelected) {
      setShowExpandedArgs(false);
    }
  }, [isSelected]);

  const scheduled = event.event_time !== undefined && event.event_time !== null;

  const timeLabel = useMemo(() => {
    const baseLabel = scheduled
      ? formatDateAndTimeFromTime(event.event_time! * 1000)
      : `(+${event.event_relative_time ?? 0} s)`;

    return event.event_time_comparator &&
      event.event_type === ARESimulationEventType.Agent
      ? `${baseLabel} [${event.event_time_comparator}]`
      : baseLabel;
  }, [
    scheduled,
    event.event_time,
    event.event_relative_time,
    event.event_time_comparator,
    event.event_type,
  ]);

  const args = useMemo(
    () =>
      action && action.args
        ? Object.entries(action.args).map(([key, value]) => (
            <React.Fragment key={`arg-${key}`}>
              <Typography color="textSecondary">{key}</Typography>
              <Typography>
                {typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value)}
              </Typography>
            </React.Fragment>
          ))
        : [],
    [action],
  );

  // @ts-ignore
  const EventNodeCardWrapper = ({
    children,
  }: {
    children: React.ReactNode;
  }) => {
    return <>{children}</>;
  };

  return (
    <>
      <Stack spacing={1} position={"relative"}>
        <Card
          elevation={6}
          sx={{
            width: NODE_WIDTH,
            height: "100%",
            overflow: "visible",
            border: `1px solid ${
              isHighlighted
                ? theme.palette.primary.main
                : isSelected
                  ? NODE_BORDER_COLOR
                  : isHovered
                    ? theme.palette.action.hover
                    : "transparent"
            }`,
          }}
          onMouseEnter={() => {
            setIsHovered(true);
          }}
          onMouseLeave={() => {
            setIsHovered(false);
          }}
          onClick={() => {
            selectNode(event.event_id);
            if (showExpandedArgs) {
              setShowExpandedArgs(false);
            }
          }}
        >
          <EventNodeCardWrapper>
            <Box
              justifyContent={"space-between"}
              alignItems={"center"}
              flexDirection={"row"}
              display={"flex"}
              sx={{
                width: "100%",
                pointerEvents: "auto",
                position: "absolute",
                top: "-32px",
                left: 0,
                gap: 1,
              }}
            >
              <Box
                sx={{
                  backgroundColor: userPreferences.annotator.enhanceReadability
                    ? palette.dark
                    : palette.main,
                  borderRadius: "6px",
                  width: "fit-content",
                  paddingX: 1,
                }}
              >
                <Typography>{config.label}</Typography>
              </Box>
              <Box
                sx={{
                  display: "flex",
                  flex: 1,
                  overflow: "hidden",
                  justifyContent: "right",
                }}
              >
                <Tooltip
                  title={isEventIdCopied ? "Copied!" : event.event_id}
                  placement="bottom-end"
                >
                  <Button
                    color="white"
                    sx={{ padding: 0.2 }}
                    onClick={handleCopyEventId}
                  >
                    <Typography
                      sx={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        display: "block",
                        cursor: "pointer",
                      }}
                    >
                      {event.event_id}
                    </Typography>
                  </Button>
                </Tooltip>
              </Box>
            </Box>
            <CardContent
              sx={{
                minHeight: action ? "156px" : "32px",
                borderRadius: 2,
                bgcolor: userPreferences.annotator.enhanceReadability
                  ? alpha(palette.main, 0.3)
                  : "transparent",
              }}
            >
              <Stack direction={"row"} alignItems={"top"} spacing={1}>
                <Avatar
                  sx={{
                    bgcolor: userPreferences.annotator.enhanceReadability
                      ? palette.dark
                      : NODE_AVATAR_BACKGROUND_COLOR,
                    color: userPreferences.annotator.enhanceReadability
                      ? theme.palette.common.white
                      : NODE_BORDER_COLOR,
                    height: 32,
                    width: 32,
                  }}
                  variant="rounded"
                >
                  {getIcon(
                    event.event_type,
                    action?.app_name ? (action.app_name as AppName) : undefined,
                  )}
                </Avatar>
                <Stack spacing={1} width="100%">
                  {action && (
                    <Stack spacing={1}>
                      <Typography
                        variant="h6"
                        sx={{ paddingLeft: TEXT_PADDING }}
                      >
                        {action?.app_name}
                      </Typography>
                      <Typography
                        fontFamily={"monospace"}
                        fontWeight={
                          userPreferences.annotator.enhanceReadability
                            ? "bold"
                            : "normal"
                        }
                        fontSize={"large"}
                        color={
                          userPreferences.annotator.enhanceReadability
                            ? theme.palette.common.white
                            : palette.light
                        }
                        sx={{ paddingLeft: TEXT_PADDING }}
                      >
                        {action?.function_name}
                      </Typography>
                      {args && (
                        <Box position="relative">
                          <motion.div
                            key={`${event.event_id}-args`}
                            style={{
                              display: "-webkit-box",
                              WebkitLineClamp: userPreferences.annotator
                                .enhanceReadability
                                ? undefined
                                : 3,
                              WebkitBoxOrient: "vertical",
                              borderRadius: theme.shape.borderRadius,
                              padding: TEXT_PADDING,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              wordBreak: "break-word",
                              minHeight: "3lh",
                              fontFamily: "monospace",
                            }}
                            whileHover={{
                              backgroundColor: theme.palette.action.hover,
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              if (!showExpandedArgs) {
                                setShowExpandedArgs(true);
                                selectNode(event.event_id);
                              } else {
                                setShowExpandedArgs(false);
                              }
                            }}
                          >
                            {userPreferences.annotator.enhanceReadability
                              ? args.map((arg, index) => (
                                  <Stack spacing={1} key={index}>
                                    {index > 0 && (
                                      <Divider sx={{ paddingTop: 1 }} />
                                    )}
                                    {arg}
                                  </Stack>
                                ))
                              : args}
                          </motion.div>
                          {/* Container for expanded args */}
                          <AnimatePresence mode="wait" initial={false}>
                            {showExpandedArgs && (
                              <motion.div
                                key="expanded-args"
                                style={{
                                  position: "absolute",
                                  overflow: "visible",
                                  top: 0,
                                  left: 0,
                                  width: "100%",
                                  borderRadius: theme.shape.borderRadius,
                                  padding: TEXT_PADDING,
                                  backgroundColor: NODE_AVATAR_BACKGROUND_COLOR,
                                  zIndex: 10,
                                  wordBreak: "break-word",
                                  fontFamily: "monospace",
                                  boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
                                  willChange: "opacity, transform",
                                  transform: "translateZ(0)",
                                  backfaceVisibility: "hidden",
                                }}
                                initial={{ opacity: 0, y: -5 }}
                                animate={{
                                  opacity: 1,
                                  y: 0,
                                  transition: {
                                    duration: 0.5,
                                    ease: "easeOut",
                                    delay: 0.05,
                                  },
                                }}
                                exit={{
                                  opacity: 0,
                                  y: -5,
                                  transition: {
                                    duration: 0.4,
                                    ease: "easeIn",
                                  },
                                }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  e.preventDefault();
                                  if (showExpandedArgs) {
                                    setShowExpandedArgs(false);
                                  }
                                }}
                              >
                                {args.map((arg, index) => (
                                  <Stack spacing={1} key={index}>
                                    {index > 0 && (
                                      <Divider sx={{ paddingTop: 1 }} />
                                    )}
                                    {arg}
                                  </Stack>
                                ))}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </Box>
                      )}
                    </Stack>
                  )}
                  <Stack spacing={1} paddingLeft={TEXT_PADDING}>
                    <Stack direction="row" alignItems={"center"} spacing={1}>
                      <AccessTimeIcon
                        fontSize="inherit"
                        htmlColor={
                          scheduled
                            ? theme.palette.text.primary
                            : theme.palette.text.secondary
                        }
                      />
                      {!scheduled && (
                        <Typography color={"textSecondary"} fontWeight={"bold"}>
                          NOT SCHEDULED
                        </Typography>
                      )}
                      <Typography color={"textPrimary"} fontWeight={"bold"}>
                        {timeLabel}
                      </Typography>
                    </Stack>
                  </Stack>
                </Stack>
              </Stack>
              <AnimatePresence>
                {(isSelected || isHovered) && (
                  <motion.div
                    key={`${event.event_id}-controls`}
                    style={{
                      position: "absolute",
                      bottom: "-32px",
                      right: 0,
                      justifyContent: "right",
                    }}
                    animate={{ opacity: 1, transition: { duration: 0.2 } }}
                    exit={{ opacity: 0, transition: { duration: 0.1 } }}
                  >
                    <EventNodeControls
                      event={event}
                      isEditable={isEditable}
                      showEditControls={showEditControls}
                      isEventIdCopied={isEventIdCopied}
                      handleCopyEventId={handleCopyEventId}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </EventNodeCardWrapper>
        </Card>
      </Stack>

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </>
  );
};

const memoizedNode = memo<typeof EventNode>(EventNode);

export default memoizedNode;

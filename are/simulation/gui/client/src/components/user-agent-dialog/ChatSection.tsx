// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloseIcon from "@mui/icons-material/Close";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { Box, IconButton, Stack, Typography, useTheme } from "@mui/material";
import { motion } from "motion/react";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { EnvironmentTimeStore } from "../../../stores/EnvironmentTimeStore";
import { useStore } from "../../../stores/Store";
import { useAppContext } from "../../contexts/AppContextProvider";
import LayoutShadowContextProvider, {
  useLayoutShadow,
} from "../../contexts/LayoutShadowContextProvider";
import { getAppNameFromToolName } from "../../utils/toolUtils";
import {
  AGENT_USER_INTERFACE_APP_NAME,
  AppName,
  ARESimulationEventType,
  EnvState,
  EventLog,
} from "../../utils/types";
import AppIcon from "../icons/AppIcon";
import OnVisible from "../OnVisible";
import { LLMInputOutputType, Message, Notification } from "./createMessageList";
import EnvironmentStatus from "./EnvironmentStatus";
import { InfoLevel } from "./InfoLevelMenu";
import { MessageComponent } from "./MessageComponent";
import { useMessageList } from "./useMessageList";
import "./UserAgentDialog.css";

const SHADOW_SCROLL_BUFFER = 5; // px threshold to show shadow
const VISIBLE_ELEMENTS_BUFFER = 5; // number of elements to load when near top
const CHAT_WIDTH = 750; // px width of chat content

function calculateIsAgentRunning(
  eventLog: EventLog,
  envState: string,
  lastMessage: Message | null,
) {
  if (envState !== EnvState.RUNNING && envState !== EnvState.PAUSED) {
    return false;
  }

  if (eventLog.length === 0) {
    return false;
  }

  // Find the last event that's not an environment event
  let lastEvent = eventLog[eventLog.length - 1];
  for (let i = eventLog.length - 1; i >= 0; i--) {
    if (eventLog[i].event_type !== ARESimulationEventType.Env) {
      lastEvent = eventLog[i];
      break;
    }
  }

  if (
    lastEvent.event_type === ARESimulationEventType.Agent &&
    lastEvent.action.app_name === AGENT_USER_INTERFACE_APP_NAME &&
    lastEvent.action.function_name === "send_message_to_user"
  ) {
    if (
      lastMessage?.type === "LLMInputOutput" &&
      !(lastMessage as LLMInputOutputType).output
    ) {
      return true;
    }

    return false;
  }

  return true;
}

function ChatSectionInternal({
  input,
  header,
}: {
  header: React.ReactNode;
  input: React.ReactNode;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const { envState, eventLog, infoLevel } = useAppContext();
  const { environmentTime } = useStore(EnvironmentTimeStore);
  const { messages, notifications } = useMessageList();
  const lastMessage = messages.length ? messages[messages.length - 1] : null;
  const isAgentRunning = useMemo(
    () => calculateIsAgentRunning(eventLog, envState, lastMessage),
    [eventLog, envState, lastMessage],
  );
  const { hasOverflowContent } = useLayoutShadow();
  const headerRef = useRef<HTMLDivElement>(null);
  const theme = useTheme();
  const failed = envState === EnvState.FAILED;

  useEffect(() => {
    // Scroll to bottom after component mounts and content is rendered
    if (bottomRef.current) {
      bottomRef.current.scrollTop = bottomRef.current.scrollHeight;
    }
  }, []);

  return (
    <Stack sx={{ width: "100%" }}>
      {header && (
        <motion.div
          ref={headerRef}
          animate={{
            boxShadow: hasOverflowContent ? theme.shadows[5] : "none",
            borderBottom: hasOverflowContent
              ? `1px solid ${theme.palette.divider}`
              : "1px solid transparent",
            zIndex: 3,
          }}
        >
          {header}
        </motion.div>
      )}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          justifyContent: "flex-end",
          width: "100%",
          marginLeft: "auto",
          marginRight: "auto",
          overflowY: "hidden",
          flexGrow: "2",
          height: "100%",
          paddingX: 2,
        }}
      >
        <MessageList
          messages={messages}
          infoLevel={infoLevel}
          isAgentRunning={isAgentRunning}
        />
        <ChatSectionNotifications
          notifications={notifications}
          environmentTime={environmentTime}
        />
        {failed && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 1,
            }}
          >
            <ErrorOutlineIcon />
            <Typography variant="h6">
              Scenario did not finish successfully.
            </Typography>
          </Box>
        )}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            maxWidth: `${CHAT_WIDTH}px`,
            margin: "0 auto",
          }}
        >
          {input}
        </Box>
      </Box>
      <div ref={bottomRef} />
    </Stack>
  );
}

const MessageList = React.memo(
  ({
    messages,
    infoLevel,
    isAgentRunning,
  }: {
    messages: ReadonlyArray<Message>;
    isAgentRunning: boolean;
    infoLevel: InfoLevel;
  }) => {
    // Start with more visible elements to avoid empty space
    const [visibleElements, setVisibleElements] = useState(10);
    const messageListRef = useRef<HTMLDivElement>(null);
    const { setHasOverflowContent } = useLayoutShadow();
    // Increase visible elements when new messages are added
    const onVisible = useCallback(() => {
      if (messages.length > visibleElements) {
        // If we have more messages than visible elements, increase the visible elements
        setVisibleElements(
          Math.min(visibleElements + VISIBLE_ELEMENTS_BUFFER, messages.length),
        );
      }
    }, [messages.length, visibleElements]);

    const checkForOverflow = useCallback(() => {
      if (messageListRef.current) {
        const hasOverflow =
          messageListRef.current.scrollHeight >
          messageListRef.current.clientHeight;

        const hasScrolledToTop =
          messageListRef.current.scrollHeight -
            (messageListRef.current.clientHeight -
              messageListRef.current.scrollTop) <
          SHADOW_SCROLL_BUFFER;

        // Only show shadow if there's overflow AND we haven't scrolled to the top
        setHasOverflowContent(hasOverflow && !hasScrolledToTop);
      } else {
        setHasOverflowContent(false);
      }
    }, [setHasOverflowContent]);

    // Handle scroll events
    const handleScroll = useCallback(() => {
      checkForOverflow();

      // Check if we're near the top of the scrollable area (which is actually
      // the oldest messages in a column-reverse layout)
      if (messageListRef.current) {
        const scrollPosition = messageListRef.current.scrollTop;
        const maxScroll =
          messageListRef.current.scrollHeight -
          messageListRef.current.clientHeight;

        // If we're within 20% of the top, load more messages
        if (
          scrollPosition > maxScroll * 0.8 &&
          visibleElements < messages.length
        ) {
          setVisibleElements((prev) => Math.min(prev + 5, messages.length));
        }
      }
    }, [checkForOverflow, messages.length, visibleElements]);

    // Run the overflow check when messages change, elements become visible, or window resizes
    useEffect(() => {
      checkForOverflow();

      // Add resize listener to check for overflow when window size changes
      window.addEventListener("resize", checkForOverflow);

      // Clean up the event listener when component unmounts
      return () => {
        window.removeEventListener("resize", checkForOverflow);
      };
    }, [messages, checkForOverflow]);

    return (
      messages.length > 0 && (
        <Box
          ref={messageListRef}
          onScroll={handleScroll}
          sx={{
            overflowY: "auto",
            overflowX: "hidden",
            display: "flex",
            flexDirection: "column-reverse",
            height: "100%",
            width: "100%",
          }}
        >
          {/* Content container with fixed width centered in the scrollable area */}
          <Stack
            sx={{
              width: "100%",
              maxWidth: `${CHAT_WIDTH}px`,
              margin: "0 auto",
              alignItems: "stretch",
              flexGrow: 1,
              flexDirection: "column-reverse",
            }}
          >
            <EnvironmentStatus isAgentRunning={isAgentRunning} />
            {messages.slice(0, visibleElements).map((message) => {
              return (
                <MessageComponent
                  key={message.id}
                  message={message}
                  showTimestamps={infoLevel.timestamps}
                />
              );
            })}
            <OnVisible onVisible={onVisible} />
          </Stack>
        </Box>
      )
    );
  },
  (prevProps, nextProps) => {
    return (
      prevProps.messages.length === nextProps.messages.length &&
      prevProps.isAgentRunning === nextProps.isAgentRunning &&
      prevProps.infoLevel === nextProps.infoLevel
    );
  },
);

const NOTIFICATION_TIMEOUT = 10; // 10 seconds

function ChatSectionNotifications({
  notifications,
  environmentTime,
}: {
  notifications: ReadonlyArray<Notification>;
  environmentTime: number;
}) {
  const [hiddenNotifications, setHiddenNotifications] = useState<
    ReadonlySet<string>
  >(new Set());
  const visibleNotifications = notifications.filter(
    (notification) =>
      environmentTime - notification.timestamp < NOTIFICATION_TIMEOUT &&
      !hiddenNotifications.has(notification.id),
  );
  const { setSelectedApp } = useAppContext();

  return (
    <Box
      sx={{
        position: "fixed",
        maxHeight: "calc(100vh - 24px)",
        height:
          visibleNotifications.length === 0
            ? 0
            : (80 + 12) * visibleNotifications.length + 50,
        top: 0,
        right: 0,
        boxSizing: "border-box",
        padding: 1,
        width: 240,
        zIndex: 2,
        overflow: "auto",
      }}
    >
      {visibleNotifications.map((notification, index) => {
        // @ts-ignore
        const content = notification.input?.content;
        const openApp = () => {
          // If toolMetadata is available, use its name for the app name
          // This ensures we open the correct app in the drawer
          const appName =
            getAppNameFromToolName(notification.toolMetadata?.name) ||
            notification.appName;

          setSelectedApp(appName as AppName, {
            extraData: {
              name: "App Function Call",
              data: {
                app: notification.appName,
                action: notification.actionName,
                input: notification.input,
                output: notification.output,
                exception: notification.exception,
                stackTrace: notification.exceptionStackTrace,
                toolMetadata: notification.toolMetadata,
              },
            },
          });
        };

        return (
          <Stack
            direction="row"
            gap={1}
            key={notification.id}
            alignItems="center"
            padding={1}
            sx={{
              position: "absolute",
              top: index * 92 + 50,
              height: 80,
              backgroundColor: "rgba(0,0,0,0.5)",
              borderRadius: 2,
              transition: "top 0.3s ease-in-out",
              width: "calc(100% - 16px)",
              cursor: "pointer",
            }}
            onClick={openApp}
          >
            <Stack
              sx={{ width: 32, height: 32 }}
              justifyContent="center"
              alignItems="center"
            >
              <AppIcon appName={notification.appName} size={16} color="white" />
            </Stack>
            <Stack direction="column">
              <Typography variant="body1" fontWeight="bold" color="white">
                {notification.appName}
              </Typography>
              {content != null && (
                <Typography
                  variant="caption"
                  color="white"
                  sx={{ wordBreak: "break-all" }}
                >
                  {content.length > 100
                    ? content.slice(0, 100) + "..."
                    : content}
                </Typography>
              )}
            </Stack>
            <IconButton
              sx={{
                position: "absolute",
                right: 0,
                top: 0,
              }}
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                setHiddenNotifications((old) =>
                  new Set(old).add(notification.id),
                );
              }}
            >
              <CloseIcon />
            </IconButton>
          </Stack>
        );
      })}
    </Box>
  );
}

export function ChatSection({
  input,
  header,
}: {
  input: React.ReactNode;
  header: React.ReactNode;
}) {
  return (
    <LayoutShadowContextProvider>
      <ChatSectionInternal input={input} header={header} />
    </LayoutShadowContextProvider>
  );
}

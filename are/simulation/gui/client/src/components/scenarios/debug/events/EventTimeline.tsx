// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import FlagIcon from "@mui/icons-material/Flag";
import ManageSearchIcon from "@mui/icons-material/ManageSearch";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import {
  FormControlLabel,
  Stack,
  Switch,
  Typography,
  useTheme,
} from "@mui/material";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAppContext } from "../../../../contexts/AppContextProvider";
import DebugCard from "../DebugCard";
import ViewModeToggle, { ViewMode } from "../ViewModeToggle";
import SpecialTimelineItem from "./SpecialTimelineItem";
import TimelineItem from "./TimelineItem";
import WebNavTimelineItem from "./WebNavTimelineItem";

interface EventTimelineProps {
  viewMode: ViewMode;
  onViewModeChange: (
    event: React.MouseEvent<HTMLElement>,
    newViewMode: ViewMode | null,
  ) => void;
}

const EventTimeline = ({ viewMode, onViewModeChange }: EventTimelineProps) => {
  const { eventLog, appsState } = useAppContext();
  const theme = useTheme();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevEventLogLengthRef = useRef(eventLog.length);
  const [autoScroll, setAutoScroll] = useState(true);

  // Process WebNavigation queries similar to EventLog.tsx
  const queries = new Map<string, Array<any>>();
  for (const app of appsState) {
    if (app?.app_name === "WebNavigation") {
      for (const [key, value] of Object.entries(app?.queries ?? {})) {
        // @ts-ignore
        queries.set(key, value);
      }
    }
  }

  // Scroll to the very bottom of the container with smooth animation
  const scrollToBottom = useCallback(() => {
    if (scrollContainerRef.current && autoScroll) {
      // Use smooth scrolling behavior for a more natural experience
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [autoScroll]);

  useEffect(() => {
    setTimeout(scrollToBottom, 500);
  }, []);

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [autoScroll, scrollToBottom]);

  // Auto-scroll to bottom when new events are added
  useEffect(() => {
    if (
      eventLog.length > prevEventLogLengthRef.current &&
      scrollContainerRef.current
    ) {
      // Use a longer delay to ensure all animations have completed
      setTimeout(scrollToBottom, 300);
    }
    prevEventLogLengthRef.current = eventLog.length;
  }, [eventLog.length]);

  // Build timeline items
  const timelineItems: Array<React.ReactNode> = [];

  // Add events and web navigation items
  eventLog.forEach((event, index) => {
    const queryId = event?.metadata?.return_value?.request_id;
    const frames = queryId ? queries.get(queryId) : null;

    timelineItems.push(<TimelineItem key={`event-${index}`} event={event} />);

    if (frames != null && frames.length > 0) {
      const stream = {
        task: frames[0].main_question,
        frames: frames,
      };
      timelineItems.push(
        <WebNavTimelineItem stream={stream} key={`webnav-${queryId}`} />,
      );
      queries.delete(queryId);
    }
  });

  // Add any remaining queries
  for (const [key, frames] of queries) {
    if (frames == null || frames.length === 0) {
      continue;
    }

    const stream = {
      task: frames[0].main_question,
      frames: frames,
    };

    timelineItems.push(
      <WebNavTimelineItem stream={stream} key={`webnav-${key}`} />,
    );
  }

  // Create a combined menu component with ViewModeToggle and Tail Logs switch
  const menu = (
    <Stack direction="row" spacing={2} alignItems="center" mr={0.5}>
      <FormControlLabel
        control={
          <Switch
            checked={autoScroll}
            onChange={(e) => {
              setAutoScroll(e.target.checked);
            }}
            size="small"
          />
        }
        label="Tail logs"
        sx={{ marginRight: 0 }}
      />
      <ViewModeToggle viewMode={viewMode} onViewModeChange={onViewModeChange} />
    </Stack>
  );

  return (
    <DebugCard
      title="Logs"
      menu={menu}
      actions={eventLog.length > 0 ? null : <div />}
    >
      <AnimatePresence>
        {eventLog.length > 0 ? (
          <motion.div
            ref={scrollContainerRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              width: "100%",
              height: "100%",
              overflowY: "auto",
            }}
          >
            <Stack
              spacing={0}
              alignItems="center"
              sx={{
                width: "100%",
                position: "relative",
              }}
            >
              <SpecialTimelineItem label="Start" icon={<PlayArrowIcon />} />
              {timelineItems}
              <SpecialTimelineItem label="Now" icon={<FlagIcon />} />
            </Stack>
          </motion.div>
        ) : (
          <Stack
            width={"100%"}
            height={"100%"}
            justifyContent={"center"}
            alignItems={"center"}
            spacing={1}
          >
            <ManageSearchIcon
              htmlColor={theme.palette.text.disabled}
              fontSize="large"
            />
            <Typography color="text.disabled">No logs</Typography>
          </Stack>
        )}
      </AnimatePresence>
    </DebugCard>
  );
};

export default EventTimeline;

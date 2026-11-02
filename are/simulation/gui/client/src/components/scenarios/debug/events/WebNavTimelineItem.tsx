// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Box } from "@mui/material";
import { motion } from "motion/react";
import { EventLogWebLogItem } from "../../../EventLogWebNavItem";
import { CARD_WIDTH, CONNECTOR_HEIGHT } from "./TimelineConstants";

interface WebNavTimelineItemProps {
  stream: any;
}

/**
 * Timeline item component for displaying web navigation events in the timeline
 */
const WebNavTimelineItem = ({ stream }: WebNavTimelineItemProps) => {
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
              bgcolor: (theme) => theme.palette.text.disabled,
            }}
          />
        </motion.div>
        <Box sx={{ width: CARD_WIDTH }}>
          <EventLogWebLogItem stream={stream} />
        </Box>
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: CONNECTOR_HEIGHT }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Box
            sx={{
              width: 2,
              height: "100%",
              bgcolor: (theme) => theme.palette.text.disabled,
            }}
          />
        </motion.div>
      </Box>
    </motion.div>
  );
};

export default WebNavTimelineItem;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Avatar, Box, Stack, Typography, useTheme } from "@mui/material";
import { motion } from "motion/react";
import { CONNECTOR_HEIGHT } from "./TimelineConstants";

interface SpecialTimelineItemProps {
  label: string;
  icon: React.ReactNode;
}

/**
 * Special timeline item component used for the "Start" and "Now" nodes in the timeline
 */
const SpecialTimelineItem = ({ label, icon }: SpecialTimelineItemProps) => {
  const theme = useTheme();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{ width: "100%" }}
    >
      <Stack
        direction={label === "Start" ? "column" : "column-reverse"}
        justifyContent="center"
        alignItems="center"
        spacing={1}
      >
        <Typography variant="h6">{label}</Typography>
        <Avatar
          sx={{
            height: 32,
            width: 32,
            color: theme.palette.text.disabled,
            bgcolor: "transparent",
            border: `2px solid ${theme.palette.text.disabled}`,
          }}
        >
          {icon}
        </Avatar>
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: CONNECTOR_HEIGHT }}
          transition={{ duration: 0.3, delay: 0.2 }}
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <Box
            sx={{
              width: 2,
              height: "100%",
              bgcolor: theme.palette.text.disabled,
            }}
          />
        </motion.div>
      </Stack>
    </motion.div>
  );
};

export default SpecialTimelineItem;

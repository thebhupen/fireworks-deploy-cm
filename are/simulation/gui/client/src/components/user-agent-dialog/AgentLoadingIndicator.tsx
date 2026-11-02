// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { ButtonBase, Tooltip, Typography } from "@mui/material";
import { motion } from "motion/react";
import { useTabs } from "../../contexts/TabsContextProvider";

export function AgentLoadingIndicator() {
  const { setSelectedTab } = useTabs();

  const handleClick = () => {
    setSelectedTab("agent-logs");
  };

  return (
    <Tooltip title="View agent logs" placement="right">
      <ButtonBase onClick={handleClick}>
        <style>
          {`
          @keyframes wave {
            0% {
              background-position: 200% 0;
            }
            100% {
              background-position: -200% 0;
            }
          }
        `}
        </style>
        <motion.div
          style={{ width: "100%" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <Typography
            sx={{
              color: "transparent",
              background:
                "linear-gradient(90deg, #999999 0%, #999999 25%, #555555 50%, #999999 75%, #999999 100%) left/200% 100%",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              animation: "wave 3s linear infinite",
              width: "fit-content",
            }}
          >
            Working
          </Typography>
        </motion.div>
      </ButtonBase>
    </Tooltip>
  );
}

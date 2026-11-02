// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Button, Stack, Tooltip, Typography } from "@mui/material";
import { motion } from "motion/react";
import React from "react";

interface SidebarButtonProps {
  label: string;
  isExpanded: boolean;
  onClick: (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  color?: "primary" | "white" | "lightgrey";
  animateIn?: boolean;
  isSelected?: boolean;
  isDisabled?: boolean;
  showTooltip?: boolean;
}

/**
 * SidebarButton component renders a button with optional icons and label.
 * It uses motion animations for smooth transitions and a tooltip for label display.
 *
 * @param {React.ReactNode} startIcon - Optional icon to display at the start of the button.
 * @param {React.ReactNode} endIcon - Optional icon to display at the end of the button.
 * @param {string} label - The text label to display on the button.
 * @param {boolean} showLabel - Determines if the label should be shown.
 * @param {function} onClick - Function to handle button click events.
 * @param {string} color - The color theme of the button, defaults to "lightgrey".
 * @param {boolean} animateIn - Determines if the label should animate in when shown, defaults to false.
 */
const SidebarButton = ({
  startIcon = null,
  endIcon = null,
  label,
  isExpanded,
  onClick,
  color = "lightgrey",
  animateIn = false,
  isSelected = false,
  isDisabled = false,
  showTooltip = true,
}: SidebarButtonProps) => {
  return (
    <motion.div layoutRoot>
      <Tooltip
        title={isExpanded || !showTooltip ? "" : label}
        placement="right"
      >
        <Button
          onClick={onClick}
          color={color}
          fullWidth
          disabled={isDisabled}
          sx={(theme) => ({
            height: "32px",
            textTransform: "none",
            justifyContent: isExpanded ? "space-between" : "center",
            paddingX: 1.5,
            minWidth: "100%",
            backgroundColor: isSelected
              ? theme.palette.action.selected
              : undefined,
          })}
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <motion.div
              style={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                width: "21px",
              }}
              layout
              transition={{ type: "tween", duration: 0.2 }}
            >
              {startIcon}
            </motion.div>
            {isExpanded ? (
              <motion.div
                initial={{ opacity: animateIn ? 0 : 1 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                }}
              >
                <Typography noWrap textOverflow={"ellipsis"}>
                  {label}
                </Typography>
              </motion.div>
            ) : null}
          </Stack>
          {isExpanded ? endIcon : null}
        </Button>
      </Tooltip>
    </motion.div>
  );
};

export default SidebarButton;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Stack, Tooltip, Typography, useTheme } from "@mui/material";
import { AnimatePresence, motion } from "motion/react";
import React from "react";

interface FormInputLabelProps {
  label: string | React.ReactNode;
  description?: string | React.ReactElement;
}

/**
 * FormInputLabel component that displays a label and an optional description icon.
 * The description is shown as a tooltip when the icon is hovered over.
 *
 * This component is meant to be inside of an MUI FormControl component.
 *
 * @param {string} label - The text label to display.
 * @param {string | React.ReactElement} [description] - Optional description to show in a tooltip.
 *
 * @returns {JSX.Element} A stack containing the label and an optional info icon with a tooltip.
 */
const FormInputLabel: React.FC<FormInputLabelProps> = ({
  label,
  description,
}) => {
  const theme = useTheme();
  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent={"space-between"}
      marginBottom={"4px"}
      height={"24px"}
    >
      {typeof label === "string" ? <Typography>{label}</Typography> : label}
      <AnimatePresence>
        {description && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Tooltip title={description} placement="left" arrow>
              <InfoOutlinedIcon
                fontSize="inherit"
                htmlColor={theme.palette.text.secondary}
                sx={{ cursor: "pointer" }}
              />
            </Tooltip>
          </motion.div>
        )}
      </AnimatePresence>
    </Stack>
  );
};

export default FormInputLabel;

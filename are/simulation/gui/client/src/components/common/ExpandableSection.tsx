// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Collapse,
  IconButton,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import React from "react";

interface ExpandableSectionProps {
  title: string;
  isExpanded: boolean;
  setExpanded: (expanded: boolean) => void;
  children: React.ReactNode;
}

export const ExpandableSection: React.FC<ExpandableSectionProps> = ({
  title,
  isExpanded,
  setExpanded,
  children,
}) => {
  const theme = useTheme();

  return (
    <Stack
      sx={{
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 1,
        padding: theme.spacing(2),
        backgroundColor: theme.palette.background.default,
      }}
    >
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Typography
          variant="h6"
          fontWeight="bold"
          gutterBottom
          color={"inherit"}
          onClick={() => setExpanded(!isExpanded)}
          sx={{ cursor: "pointer", flexGrow: 1 }}
        >
          {title}
        </Typography>
        <Stack direction="row" alignItems="center">
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!isExpanded);
            }}
          >
            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Stack>
      </Stack>
      <Collapse in={isExpanded}>{children}</Collapse>
    </Stack>
  );
};

export default ExpandableSection;

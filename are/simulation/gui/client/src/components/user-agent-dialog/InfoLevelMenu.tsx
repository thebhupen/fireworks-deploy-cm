// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import TuneIcon from "@mui/icons-material/Tune";
import {
  Checkbox,
  IconButton,
  Menu,
  MenuItem,
  PopoverOrigin,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";

import { useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";

interface InfoLevelMenuProps {
  color?: string;
  anchorOrigin?: PopoverOrigin;
  transformOrigin?: PopoverOrigin;
}

export type InfoLevel = {
  errors: boolean;
  timestamps: boolean;
  thoughts: boolean;
  actions: boolean;
  results: boolean;
  plans: boolean;
  facts: boolean;
  llmOutputs: boolean;
  environment: boolean;
};

export function InfoLevelMenu({
  color,
  anchorOrigin,
  transformOrigin,
}: InfoLevelMenuProps) {
  const { infoLevel, setInfoLevel } = useAppContext();
  const [isOpen, setIsOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const theme = useTheme();

  return (
    <>
      <Tooltip title="Info level">
        <IconButton
          size="small"
          onClick={(e) => {
            setAnchorEl(e.currentTarget);
            setIsOpen(true);
          }}
          color="lightgrey"
          sx={{ border: `1px solid ${theme.palette.divider}` }}
        >
          <TuneIcon htmlColor={color} />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={anchorEl}
        open={isOpen}
        onClose={() => {
          setIsOpen(false);
          setAnchorEl(null);
        }}
        anchorOrigin={anchorOrigin}
        transformOrigin={transformOrigin}
      >
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, errors: !infoLevel.errors });
          }}
        >
          <Typography>Errors</Typography>
          <Checkbox checked={infoLevel.errors} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, timestamps: !infoLevel.timestamps });
          }}
        >
          <Typography>Timestamps</Typography>
          <Checkbox checked={infoLevel.timestamps} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, thoughts: !infoLevel.thoughts });
          }}
        >
          <Typography>Thoughts</Typography>
          <Checkbox checked={infoLevel.thoughts} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, actions: !infoLevel.actions });
          }}
        >
          <Typography>Actions</Typography>
          <Checkbox checked={infoLevel.actions} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, environment: !infoLevel.environment });
          }}
        >
          <Typography>Environment</Typography>
          <Checkbox checked={infoLevel.environment} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, facts: !infoLevel.facts });
          }}
        >
          <Typography>Facts</Typography>
          <Checkbox checked={infoLevel.facts} />
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoLevel({ ...infoLevel, plans: !infoLevel.plans });
          }}
        >
          <Typography>Plans</Typography>
          <Checkbox checked={infoLevel.plans} />
        </MenuItem>
      </Menu>
    </>
  );
}

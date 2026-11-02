// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CodeIcon from "@mui/icons-material/Code";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
  alpha,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Container,
  Drawer,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import React, { useState } from "react";
import { ARESimulationEvent } from "../../utils/types.js";
import JSONView, { JSONType } from "../JSONView";

type EventNodeControlsProps = {
  event: ARESimulationEvent;
  // @ts-ignore
  isEditable: boolean;
  // @ts-ignore
  showEditControls: boolean;
  isEventIdCopied: boolean;
  handleCopyEventId: () => void;
};

const EventNodeControls = ({
  event,
  // @ts-ignore
  isEditable,
  // @ts-ignore
  showEditControls,
  isEventIdCopied,
  handleCopyEventId,
}: EventNodeControlsProps): React.ReactNode => {
  const theme = useTheme();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  let extraControls = null;

  return (
    <>
      <ButtonGroup
        variant="text"
        size="small"
        color="lightgrey"
        sx={{
          backgroundColor: alpha(theme.palette.background.default, 0.8),
        }}
      >
        {extraControls}
        <Tooltip title="Event Details">
          <Button onClick={() => setIsDrawerOpen(true)}>
            <CodeIcon fontSize="small" />
          </Button>
        </Tooltip>
        <Tooltip title={isEventIdCopied ? "Copied!" : "Copy Event ID"}>
          <Button onClick={handleCopyEventId}>
            <ContentCopyIcon fontSize="small" />
          </Button>
        </Tooltip>
      </ButtonGroup>
      <Drawer
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
        }}
        title={`Event Details: ${event.event_type}`}
        anchor="right"
      >
        <Toolbar>
          <Typography>{event.event_id}</Typography>
        </Toolbar>
        <Container sx={{ width: "50vw" }}>
          <Stack spacing={2}>
            <Typography variant="h5">Raw Data</Typography>
            <Card>
              <CardContent>
                <JSONView json={event as unknown as JSONType} />
              </CardContent>
            </Card>
          </Stack>
        </Container>
      </Drawer>
    </>
  );
};

export default EventNodeControls;

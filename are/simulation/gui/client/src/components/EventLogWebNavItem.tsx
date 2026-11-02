// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import LanguageIcon from "@mui/icons-material/Language";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import TimelineConnector from "@mui/lab/TimelineConnector";
import TimelineContent from "@mui/lab/TimelineContent";
import TimelineItem from "@mui/lab/TimelineItem";
import TimelineOppositeContent from "@mui/lab/TimelineOppositeContent";
import TimelineSeparator from "@mui/lab/TimelineSeparator";
import { Button, Drawer, Typography } from "@mui/material";
import * as React from "react";
import { useState } from "react";
import JSONView from "./JSONView";
import type { WebNavStream } from "./webnav/WebNav";

export function EventLogWebLogItem({
  stream,
}: {
  stream: WebNavStream;
}): null | React.ReactNode {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  if (stream.frames.length === 0) {
    return null;
  }

  const now = new Date(stream.frames[0].timestamp).toISOString();
  const date = now.length > 23 ? now.slice(0, 10) : now;
  const time = now.length > 23 ? now.slice(11, 23) : "";

  return (
    <TimelineItem position={"right"}>
      <TimelineOppositeContent
        style={{ overflowWrap: "anywhere" }}
        sx={{ m: "auto 0" }}
        align="right"
        variant="body2"
      >
        {date}
        <br />
        {time}
      </TimelineOppositeContent>
      <TimelineSeparator>
        <TimelineConnector />
        <div
          style={{
            position: "relative",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            border: "2px solid #1976d2",
            borderRadius: 20,
            padding: 4,
          }}
        >
          <SmartToyIcon />
          <LanguageIcon />
        </div>
        <TimelineConnector />
      </TimelineSeparator>
      <TimelineContent
        sx={{ py: "12px", px: 2 }}
        style={{ overflowWrap: "anywhere" }}
      >
        <Button
          variant="text"
          color="primary"
          size="small"
          style={{ textAlign: "inherit" }}
          onClick={() => {
            setIsDrawerOpen(true);
          }}
        >
          <div>
            <Typography variant="h6" component="span">
              WEBNAV
            </Typography>
            <Typography variant="h6" style={{ color: "#4f94f4", fontSize: 14 }}>
              {stream.task}
            </Typography>
          </div>
        </Button>
        <Drawer
          anchor="right"
          open={isDrawerOpen}
          onClose={() => {
            setIsDrawerOpen(false);
          }}
          PaperProps={{
            sx: {
              width: 400,
              padding: 2,
            },
          }}
        >
          <Typography variant="h6" sx={{ marginBottom: 2 }}>
            Completed Event Details
          </Typography>
          <div className="drawer-content-padded">
            <h3>Query</h3>
            <JSONView json={stream as any} />
          </div>
        </Drawer>
      </TimelineContent>
    </TimelineItem>
  );
}

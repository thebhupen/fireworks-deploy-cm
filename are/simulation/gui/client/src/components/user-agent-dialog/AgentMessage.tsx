// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CodeIcon from "@mui/icons-material/Code";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import ViewListIcon from "@mui/icons-material/ViewList";
import {
  alpha,
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  ListItemIcon,
  Menu,
  MenuItem,
  Stack,
  useTheme,
} from "@mui/material";
import { GridCloseIcon } from "@mui/x-data-grid";
import printJS from "print-js";
import * as React from "react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useTabs } from "../../contexts/TabsContextProvider";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import { AgentIcon } from "../icons/AgentIcon";
import { AgentUserMessage } from "./createMessageList";
import { downloadMarkdown } from "./exportMarkdown";

export default function AgentMessage({
  message,
  showTimestamps,
}: {
  message: AgentUserMessage;
  showTimestamps: boolean;
}): React.ReactNode {
  const elementRef = React.useRef<HTMLDivElement>(null);
  const originalContent: string = message.content;
  const trimmedContent: string = originalContent.replace("DETAILED_ANSWER", "");
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const { scenario } = useAppContext();
  const { setSelectedTab } = useTabs();
  const theme = useTheme();
  const regex: RegExp = /<embed>(.*?)<\/embed>/;
  const match: RegExpMatchArray | null = message.content.match(regex);
  const url: string | null = match ? match[1] : null;
  const content: string = trimmedContent.replace(regex, "");
  const uiIframe = (
    <iframe
      src={url ?? ""}
      style={{
        width: "90%",
        aspectRatio: "1 / 1",
      }}
    />
  );

  const [isUIFullScreen, setUIFullScreen] = useState(false);

  let showAgentIcon = false;

  if (!content) {
    return null;
  }

  return (
    <>
      {showTimestamps && (
        <Box
          sx={{
            color: alpha(theme.palette.text.secondary, 0.8),
            fontSize: "12px",
            marginLeft: 5,
          }}
        >
          {formatDateAndTimeFromTime(message.timestamp * 1000)}
        </Box>
      )}
      {url && (
        <>
          <IconButton
            onClick={() => setUIFullScreen(true)}
            style={{
              alignSelf: "flex-end",
              marginBottom: "34px",
              marginRight: "30px",
              width: "30px",
            }}
          >
            <FullscreenIcon />
          </IconButton>
          <Box sx={{ display: "flex", justifyContent: "center" }}>
            {uiIframe}
          </Box>
          <Dialog
            fullScreen={true}
            open={isUIFullScreen}
            style={{ padding: "50px" }}
          >
            <DialogTitle
              style={{ display: "flex", justifyContent: "flex-end" }}
            >
              <IconButton onClick={() => setUIFullScreen(false)}>
                <GridCloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent
              style={{
                display: "flex",
                justifyContent: "center",
                overflow: "auto",
                paddingBottom: "50px",
              }}
            >
              {uiIframe}
            </DialogContent>
          </Dialog>
        </>
      )}
      <Stack
        direction="row"
        sx={{
          display: "flex",
          gap: 1,
          position: "relative",
          maxWidth: "85%",
          alignItems: "center",
          paddingTop: 1,
        }}
      >
        <IconButton
          onClick={(event) => {
            setAnchorEl(event.currentTarget);
          }}
          sx={{
            minWidth: "32px",
            opacity: showAgentIcon ? 1 : 0,
          }}
        >
          <AgentIcon size={14} />
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          onClose={() => {
            setAnchorEl(null);
          }}
          open={anchorEl != null}
        >
          <MenuItem
            onClick={() => {
              setAnchorEl(null);
              downloadMarkdown({
                markdown: message.content,
                filename: scenario?.scenarioId ?? "scenario",
              });
            }}
          >
            <ListItemIcon>
              <CodeIcon fontSize="small" />
            </ListItemIcon>
            Export as Markdown
          </MenuItem>
          <MenuItem
            onClick={() => {
              setAnchorEl(null);
              const element = elementRef.current;

              if (!element) {
                return;
              }

              printJS({
                printable: element,
                type: "html",
                font_size: "",
              });
            }}
          >
            <ListItemIcon>
              <PictureAsPdfIcon fontSize="small" />
            </ListItemIcon>
            Export PDF
          </MenuItem>
          <MenuItem
            onClick={() => {
              setAnchorEl(null);
              setSelectedTab("agent-logs");
            }}
          >
            <ListItemIcon>
              <ViewListIcon fontSize="small" />
            </ListItemIcon>
            View Agent Logs
          </MenuItem>
        </Menu>
        <Box ref={elementRef} sx={{ fontSize: "14px" }}>
          <ReactMarkdown
            components={{
              p: ({ ...props }) => (
                <p
                  style={{ marginTop: "4px", marginBottom: "4px" }}
                  {...props}
                />
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </Box>
      </Stack>
    </>
  );
}

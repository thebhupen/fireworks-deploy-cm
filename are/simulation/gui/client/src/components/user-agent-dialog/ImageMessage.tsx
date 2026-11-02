// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import { Box, Dialog, IconButton, Typography } from "@mui/material";
import { useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { getSessionRoot } from "../../utils/FileSystemUtils";
import FileSystemImageLoader from "../common/FileSystemImageLoader";
import { ImageMessageType } from "./createMessageList";

export default function ImageMessage({
  message,
}: {
  message: ImageMessageType;
}) {
  const { appsState, filesystemPath } = useAppContext();
  const [open, setOpen] = useState(false);

  // Get the filesystem app name from the apps state
  const filesystemApp = appsState.find((app) =>
    ["Files", "SandboxLocalFileSystem", "VirtualFileSystem"].includes(
      app.app_name,
    ),
  );
  const filesystemAppName = filesystemApp?.app_name;

  // Convert the image source path to the server path format
  // Remove the filesystem path prefix if present to get the relative path
  let serverPath = message.src;
  if (filesystemPath && message.src.startsWith(filesystemPath)) {
    serverPath = message.src.replace(filesystemPath, "");
  }
  // Ensure path starts with /
  if (!serverPath.startsWith("/")) {
    serverPath = "/" + serverPath;
  }

  if (!filesystemAppName) {
    return null;
  }

  const sessionRoot = getSessionRoot(filesystemPath ?? "");
  const displayPath =
    message.src.split(sessionRoot).slice(-1).pop() || message.src;

  return (
    <>
      <Box
        onClick={() => setOpen(true)}
        sx={{
          marginTop: "8px",
          marginLeft: "35px",
          overflow: "hidden",
        }}
      >
        <FileSystemImageLoader
          filePath={serverPath}
          filesystemAppName={filesystemAppName}
          width="100%"
          style={{
            maxWidth: "200px",
            maxHeight: "150px",
            flex: 1,
            borderRadius: "8px",
            objectFit: "cover",
            cursor: "pointer",
            border: "1px solid #FFFFFF1A",
          }}
          alt="Image attachment"
        />
      </Box>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        style={{ maxHeight: "100%" }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginLeft: 2,
          }}
        >
          <Typography variant="caption" component="div">
            <b>Attachment:</b> {displayPath}
          </Typography>
          <IconButton onClick={() => setOpen(false)}>
            <CloseOutlinedIcon />
          </IconButton>
        </Box>
        <FileSystemImageLoader
          filePath={serverPath}
          filesystemAppName={filesystemAppName}
          width="100%"
          style={{ width: "100%" }}
          alt="Image attachment"
        />
      </Dialog>
    </>
  );
}

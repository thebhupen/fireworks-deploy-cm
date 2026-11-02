// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import AttachFileIcon from "@mui/icons-material/AttachFile";
import { useAppContext } from "../../contexts/AppContextProvider";
import { parseFilePath } from "../../utils/FileSystemUtils";
import { DocumentMessageType } from "./createMessageList";

export default function DocumentMessage({
  message,
}: {
  message: DocumentMessageType;
}) {
  const { filesystemPath } = useAppContext();
  const file = parseFilePath(message.src, filesystemPath);

  return file.kind === "ok" ? (
    <a
      href={file.value}
      target="_blank"
      style={{
        display: "flex",
        alignItems: "center",
        cursor: "pointer",
        marginTop: "-10px",
        marginLeft: "35px",
        marginBottom: "20px",
      }}
    >
      {message.src.split("/").pop()}
      <AttachFileIcon />
    </a>
  ) : null;
}

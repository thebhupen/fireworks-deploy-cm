// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import FileSystemSection from "./FileSystemSection";
import { FileSystemApp } from "./types";

function FileSystemTab({ state }: { state: FileSystemApp }): React.ReactNode {
  const NO_FILES_FOUND = "No files found.";
  const files = state.files;

  if (!state || !files) {
    return <div>{NO_FILES_FOUND}</div>;
  }

  if (!files || Object.keys(files).length === 0) {
    return <div>{NO_FILES_FOUND}</div>;
  }

  return (
    <FileSystemSection files={files} filesystemAppName={state.app_name!} />
  );
}

export default FileSystemTab;

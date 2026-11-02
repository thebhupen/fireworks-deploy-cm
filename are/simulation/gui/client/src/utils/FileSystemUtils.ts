// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { maybeUserDevServerPath } from "./PathUtils";
import { err, ok, Result } from "./Result";

export function parseFilePath(
  src: string,
  filesystemPath: string | null,
): Result<string, string> {
  if (filesystemPath == null) {
    return err("no-filesystem-path");
  }

  return ok(normalizePath(src, filesystemPath));
}

export function getSessionRoot(filesystemPath: string): string {
  return filesystemPath.split("/").slice(-2).join("/");
}

export function normalizePath(path: string, filesystemPath: string): string {
  const sessionRoot = getSessionRoot(filesystemPath);

  if (path.startsWith(filesystemPath)) {
    return maybeUserDevServerPath(
      `/files/${sessionRoot}${path.replace(filesystemPath, "")}`,
    );
  } else {
    return maybeUserDevServerPath(`/files/${sessionRoot}/${path}`);
  }
}

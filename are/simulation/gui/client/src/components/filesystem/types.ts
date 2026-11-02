// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AppName } from "../../utils/types";

export interface FileSystemApp {
  app_name?: AppName;
  files: FileNode;
}

export interface FileNode {
  name: string;
  type: string;
  path: string;
  children?: FileNode[];
}

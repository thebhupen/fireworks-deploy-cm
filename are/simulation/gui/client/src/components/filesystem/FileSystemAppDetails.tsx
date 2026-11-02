// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { FileNode, FileSystemApp } from "./types";

export const FileSystemAppDetails = ({ app }: { app: FileSystemApp }) => {
  const countFiles = (directory: FileNode) => {
    let fileCount = 0;

    const recursiveCountFiles = (node: FileNode) => {
      if (node.type === "file") {
        fileCount++;
      } else if (node.type === "directory" && node.children) {
        node.children.forEach((child) => recursiveCountFiles(child));
      }
    };

    recursiveCountFiles(directory);
    return fileCount;
  };

  const countFolders = (directory: FileNode) => {
    let folderCount = 0;

    const recursiveCountFolders = (node: FileNode) => {
      if (node.type === "directory") {
        folderCount++;
        if (node.children) {
          node.children.forEach((child) => recursiveCountFolders(child));
        }
      }
    };

    recursiveCountFolders(directory);
    return folderCount;
  };

  const totalFiles = countFiles(app.files);
  const totalFolders = countFolders(app.files);

  return (
    <>
      <div>Files: {totalFiles}</div>
      <div>Folders: {totalFolders}</div>
    </>
  );
};

export default FileSystemAppDetails;

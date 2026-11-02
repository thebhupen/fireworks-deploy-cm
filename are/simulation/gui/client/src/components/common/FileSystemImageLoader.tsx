// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Box, CircularProgress } from "@mui/material";
import React, { Suspense, useContext } from "react";
import {
  graphql,
  PreloadedQuery,
  usePreloadedQuery,
  useQueryLoader,
} from "react-relay";
import SessionIdContext from "../../contexts/SessionIdContext";
import Image from "./Image";
import { FileSystemImageLoaderGetFileContentQuery } from "./__generated__/FileSystemImageLoaderGetFileContentQuery.graphql";

const FileContentQuery = graphql`
  query FileSystemImageLoaderGetFileContentQuery(
    $sessionId: String!
    $filesystemAppName: String!
    $filePath: String!
  ) {
    getFileContent(
      sessionId: $sessionId
      filesystemAppName: $filesystemAppName
      filePath: $filePath
    )
  }
`;

interface FileSystemImageLoaderProps {
  filePath: string;
  filesystemAppName: string;
  width?: string;
  style?: React.CSSProperties;
  alt?: string;
}

export default function FileSystemImageLoader({
  filePath,
  filesystemAppName,
  width = "100%",
  style,
  alt,
}: FileSystemImageLoaderProps) {
  const sessionId = useContext(SessionIdContext);
  const [fileContentQueryReference, loadFileContentQuery] =
    useQueryLoader<FileSystemImageLoaderGetFileContentQuery>(FileContentQuery);

  // Load the image data on mount
  React.useEffect(() => {
    if (sessionId && filesystemAppName && filePath) {
      loadFileContentQuery({
        sessionId,
        filesystemAppName,
        filePath,
      });
    }
  }, [sessionId, filesystemAppName, filePath, loadFileContentQuery]);

  if (!fileContentQueryReference) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        style={style}
      >
        <CircularProgress size={24} />
      </Box>
    );
  }

  return (
    <Suspense
      fallback={
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          style={style}
        >
          <CircularProgress size={24} />
        </Box>
      }
    >
      <ImageContent
        fileContentQueryReference={fileContentQueryReference}
        width={width}
        style={style}
        alt={alt}
        filePath={filePath}
      />
    </Suspense>
  );
}

interface ImageContentProps {
  fileContentQueryReference: PreloadedQuery<FileSystemImageLoaderGetFileContentQuery>;
  width: string;
  style?: React.CSSProperties;
  alt?: string;
  filePath: string;
}

function ImageContent({
  fileContentQueryReference,
  width,
  style,
  alt,
  filePath,
}: ImageContentProps) {
  const data = usePreloadedQuery(FileContentQuery, fileContentQueryReference);

  if (!data.getFileContent) {
    return <div>No image content available</div>;
  }

  // Extract file extension from path
  const fileExtension = filePath.split(".").pop()?.toLowerCase() || "png";

  return (
    <Image
      src={`data:image/${fileExtension};base64,${data.getFileContent}`}
      width={width}
      style={style}
      alt={alt}
    />
  );
}

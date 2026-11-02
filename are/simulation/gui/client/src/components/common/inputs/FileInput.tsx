// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloseIcon from "@mui/icons-material/Close";
import { Box, IconButton, Typography } from "@mui/material";
import {
  DragEvent,
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

export interface FileInputHandle {
  openFileDialog: () => void;
}

interface FileInputProps {
  onFileSelected: (file: File | null) => void;
  accept?: string;
  label?: string;
  selectedFile?: File | null;
}

const FileInput = forwardRef<FileInputHandle, FileInputProps>(
  (
    {
      onFileSelected,
      accept = "*/*",
      label = "Upload file",
      selectedFile = null,
    },
    ref,
  ) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isDragging, setIsDragging] = useState(false);

    // Expose the openFileDialog method to the parent component
    useImperativeHandle(ref, () => ({
      openFileDialog: () => {
        fileInputRef.current?.click();
      },
    }));

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        onFileSelected(file);
      }
    };

    const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(true);
    };

    const handleDragLeave = () => {
      setIsDragging(false);
    };

    const handleDrop = (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files?.[0];
      if (file) {
        onFileSelected(file);
      }
    };

    const handleRemoveFile = (e: React.MouseEvent) => {
      e.stopPropagation();
      onFileSelected(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    };

    // Clear the HTML input element when selectedFile becomes null from parent
    useEffect(() => {
      if (selectedFile === null && fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }, [selectedFile]);

    return (
      <Box>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={accept}
          style={{ display: "none" }}
        />
        <Box
          sx={(theme) => ({
            border: `2px ${isDragging || !selectedFile ? "dashed" : "solid"}`,
            borderColor: isDragging ? "primary.main" : theme.palette.divider,
            borderRadius: 1,
            padding: 4,
            textAlign: "center",
            backgroundColor: isDragging
              ? theme.palette.action.hover
              : "transparent",
            cursor: "pointer",
            transition: "all 0.2s",
          })}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <Box display="flex" alignItems="center" justifyContent="center">
              <Typography variant="body2" color="primary">
                {selectedFile.name}
              </Typography>
              <IconButton
                size="small"
                onClick={handleRemoveFile}
                sx={{ ml: 1 }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          ) : (
            <>
              <Typography variant="body1" mb={1}>
                {label}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Drag and drop a file here, or click to select
              </Typography>
            </>
          )}
        </Box>
      </Box>
    );
  },
);

export default FileInput;

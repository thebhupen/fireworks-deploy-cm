// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
  Alert,
  CircularProgress,
} from "@mui/material";
import { useState, useContext } from "react";
import { graphql, useMutation } from "react-relay";
import SessionIdContext from "../../contexts/SessionIdContext";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import { FileUploadDialogUploadFileMutation } from "./__generated__/FileUploadDialogUploadFileMutation.graphql";

const UploadFileMutation = graphql`
  mutation FileUploadDialogUploadFileMutation(
    $sessionId: String!
    $filesystemAppName: String!
    $fileName: String!
    $fileContent: String!
    $destinationPath: String!
  ) {
    uploadFile(
      sessionId: $sessionId
      filesystemAppName: $filesystemAppName
      fileName: $fileName
      fileContent: $fileContent
      destinationPath: $destinationPath
    )
  }
`;

interface FileUploadDialogProps {
  open: boolean;
  onClose: () => void;
  filesystemAppName: string;
  onUploadSuccess?: () => void;
}

/**
 * Dialog component for uploading files to the filesystem.
 * Allows users to select a file, choose a destination path, and upload it.
 */
function FileUploadDialog({
  open,
  onClose,
  filesystemAppName,
  onUploadSuccess,
}: FileUploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [destinationPath, setDestinationPath] = useState<string>("/");
  const [error, setError] = useState<string | null>(null);

  const sessionId = useContext(SessionIdContext);
  const { notify } = useNotifications();
  const [commitUpload, isUploading] =
    useMutation<FileUploadDialogUploadFileMutation>(UploadFileMutation);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDestinationChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setDestinationPath(event.target.value);
  };

  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix (e.g., "data:image/png;base64,")
        const base64Content = result.split(",")[1];
        resolve(base64Content);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file to upload");
      return;
    }

    if (!destinationPath.trim()) {
      setError("Please specify a destination path");
      return;
    }

    try {
      setError(null);

      // Convert file to base64
      const base64Content = await convertFileToBase64(selectedFile);

      // Ensure destination path starts with /
      let normalizedPath = destinationPath.trim();
      if (!normalizedPath.startsWith("/")) {
        normalizedPath = "/" + normalizedPath;
      }

      commitUpload({
        variables: {
          sessionId,
          filesystemAppName,
          fileName: selectedFile.name,
          fileContent: base64Content,
          destinationPath: normalizedPath,
        },
        onCompleted: (response) => {
          if (response.uploadFile) {
            // Show success notification
            notify({
              message: `File "${selectedFile.name}" uploaded successfully!`,
              type: "success",
            });

            // Reset form and close dialog
            setSelectedFile(null);
            setDestinationPath("/");
            const fileInput = document.getElementById(
              "file-upload-input",
            ) as HTMLInputElement;
            if (fileInput) {
              fileInput.value = "";
            }

            // Close dialog and trigger callback
            onClose();
            if (onUploadSuccess) {
              onUploadSuccess();
            }
          } else {
            setError("Upload failed. Please try again.");
          }
        },
        onError: (error) => {
          setError(`Upload failed: ${error.message}`);
        },
      });
    } catch (error) {
      setError(
        `Failed to process file: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setDestinationPath("/");
    setError(null);
    // Reset file input
    const fileInput = document.getElementById(
      "file-upload-input",
    ) as HTMLInputElement;
    if (fileInput) {
      fileInput.value = "";
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={1}>
          <CloudUploadIcon />
          <Typography variant="h6">Upload File</Typography>
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Select File
            </Typography>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ height: 56, justifyContent: "flex-start" }}
            >
              {selectedFile ? selectedFile.name : "Choose file..."}
              <input
                id="file-upload-input"
                type="file"
                hidden
                onChange={handleFileSelect}
              />
            </Button>
            {selectedFile && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 1, display: "block" }}
              >
                Size: {(selectedFile.size / 1024).toFixed(1)} KB
              </Typography>
            )}
          </Box>

          <TextField
            label="Destination Path"
            value={destinationPath}
            onChange={handleDestinationChange}
            fullWidth
            placeholder="/path/to/destination"
            helperText="Specify the directory where the file should be uploaded (e.g., /documents, /images)"
          />

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Target Filesystem
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {filesystemAppName}
            </Typography>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={isUploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={!selectedFile || isUploading}
          startIcon={
            isUploading ? <CircularProgress size={20} /> : <CloudUploadIcon />
          }
        >
          {isUploading ? "Uploading..." : "Upload"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default FileUploadDialog;

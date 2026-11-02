// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { SUPPORTED_IMAGE_FORMATS } from "../components/user-agent-dialog/constants";

// Image extension regex for file validation
export const IMAGE_EXTENSION_REGEX = new RegExp(
  `\\.(${SUPPORTED_IMAGE_FORMATS.join("|")})$`,
  "i",
);
// File size limits in bytes
const MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
const MAX_TOTAL_ATTACHMENTS_SIZE_BYTES = 20 * 1024 * 1024; // 20MB per message

/**
 * Reads a file as text and returns a promise that resolves with the file content as a string.
 *
 * @param file - The file to be read, provided as a Blob.
 * @returns A promise that resolves with the file content as a string.
 */
export const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsText(file);
  });
};

export function validateFileType(file: File): boolean {
  return IMAGE_EXTENSION_REGEX.test(file.name.toLowerCase());
}

export function validateFileSize(file: File): boolean {
  return file.size <= MAX_ATTACHMENT_SIZE_BYTES;
}

export function validateFileAttachment(file: File): {
  isValid: boolean;
  error?: string;
} {
  // Check if file type is supported
  if (!validateFileType(file)) {
    return {
      isValid: false,
      error: `File type not supported: ${file.name}`,
    };
  }

  // Check file size
  if (!validateFileSize(file)) {
    const maxSizeMB = MAX_ATTACHMENT_SIZE_BYTES / (1024 * 1024);
    const actualSizeMB = (file.size / (1024 * 1024)).toFixed(1);

    return {
      isValid: false,
      error: `File "${file.name}" is too large (${actualSizeMB}MB). Maximum file size is ${maxSizeMB}MB.`,
    };
  }

  return { isValid: true };
}

export function validateTotalSize(files: File[]): {
  isValid: boolean;
  error?: string;
} {
  const totalSize = files.reduce((sum, file) => sum + file.size, 0);

  if (totalSize > MAX_TOTAL_ATTACHMENTS_SIZE_BYTES) {
    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);
    const maxTotalSizeMB = MAX_TOTAL_ATTACHMENTS_SIZE_BYTES / (1024 * 1024);

    return {
      isValid: false,
      error: `Total attachment size is too large (${totalSizeMB}MB). Maximum total size is ${maxTotalSizeMB}MB per message.`,
    };
  }

  return { isValid: true };
}

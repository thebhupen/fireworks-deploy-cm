// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

/**
 * Strips the app name prefix from a tool name.
 * Tool names are often prefixed with the app name followed by "__".
 * This function removes that prefix if it matches the provided app name.
 *
 * @param toolName - The full name of the tool
 * @param appName - The name of the app
 * @returns The tool name without the app name prefix
 */
export function stripAppNamePrefix(toolName: string, appName: string): string {
  const parts = toolName.split("__");
  // Only remove the prefix if it matches the current app name
  if (parts.length > 1 && parts[0] === appName) {
    return parts[1];
  }
  return toolName;
}

export function getAppNameFromToolName(
  toolName: string | null | undefined,
): string | null | undefined {
  if (toolName == null) {
    return null;
  }
  const parts = toolName.split("__");
  if (parts.length > 1) {
    return parts[0];
  }
  return "";
}

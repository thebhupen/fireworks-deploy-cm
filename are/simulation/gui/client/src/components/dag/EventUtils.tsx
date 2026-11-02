// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

export const getPipeSeparatedTypes = (type: string): Array<string> => {
  return type?.split(/(?![^\[\]\(\)\<\>]*[\]\)\>\]])\|/).map((s) => s.trim());
};

export const getIsOptional = (pipeSeparatedTypes: Array<string>): boolean => {
  return pipeSeparatedTypes.length > 1 && pipeSeparatedTypes.includes("None");
};

export const getIsListType = (pipeSeparatedTypes: Array<string>): boolean => {
  // Will be considered a list type if at least one of the types is a list type.
  return pipeSeparatedTypes.some((t) => /^list\[(.*)\]$/.test(t));
};

export const getUnderlyingType = (
  pipeSeparatedTypes: Array<string>,
): string => {
  return pipeSeparatedTypes.filter((t) => t !== "None").join(" | ");
};

export const getUnderlyingListType = (
  pipeSeparatedTypes: Array<string>,
): string | null => {
  for (const type of pipeSeparatedTypes) {
    const underlyingType = type.match(/^list\[(.*)\]$/)?.[1];
    if (underlyingType !== null && underlyingType !== undefined) {
      // Return the first list type.
      return underlyingType;
    }
  }
  return null;
};

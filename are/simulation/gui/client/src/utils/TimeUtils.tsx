// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

export function formatDateAndTimeFromTime(secondTime: number): string {
  return new Date(secondTime).toLocaleString("en-US", {
    timeZone: "UTC",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatDateFromTime(secondTime: number): string {
  return new Date(secondTime).toLocaleString("en-US", {
    timeZone: "UTC",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function formatLocalDateFromTime(secondTime: number): string {
  return new Date(secondTime).toLocaleString("en-US", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatISODateFromTime(secondTime: number): string {
  return new Date(secondTime).toISOString();
}

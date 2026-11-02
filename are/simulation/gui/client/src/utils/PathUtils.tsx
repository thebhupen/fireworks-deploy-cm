// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { BASE_URL } from "./const";

/**
 * Adjusts a path to include the user dev server prefix when running in dev mode
 * @param path The path to adjust
 * @returns The path with the dev server prefix if needed
 */
export function maybeUserDevServerPath(path: string): string {
  return `${BASE_URL}${path}`;
}

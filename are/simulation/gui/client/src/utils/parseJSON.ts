// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { err, ok, Result } from "./Result";

export function parseJSON<T extends object>(
  content: string,
): Result<T, "parse-error"> {
  try {
    return ok(JSON.parse(content));
  } catch (e) {
    return err("parse-error");
  }
}

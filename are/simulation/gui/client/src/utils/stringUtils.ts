// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

export const capitalize = (s: string): string => {
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
};

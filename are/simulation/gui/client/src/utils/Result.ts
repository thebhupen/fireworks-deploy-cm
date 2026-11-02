// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

export type Err<E> = { kind: "err"; error: E };
export type Ok<T> = { kind: "ok"; value: T };
export type Result<T, E> = Ok<T> | Err<E>;

export function ok<T>(value: T): Ok<T> {
  return { kind: "ok", value };
}

export function err<E>(error: E): Err<E> {
  return { kind: "err", error };
}

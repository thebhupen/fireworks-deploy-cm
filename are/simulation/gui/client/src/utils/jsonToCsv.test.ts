// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { describe, expect, it } from "vitest";
import { jsonToCsv } from "./jsonToCsv";

describe("jsonToCsv", () => {
  it("should convert a simple JSON object to Csv", () => {
    const json = {
      messages: [
        { from: "John", to: "Jane", subject: "Hello" },
        { from: "Jane", to: "John", subject: "Hi" },
      ],
    };
    const csv = jsonToCsv(json.messages);
    expect(csv).toEqual([
      ["from", "to", "subject"],
      ["John", "Jane", "Hello"],
      ["Jane", "John", "Hi"],
    ]);
  });

  it("should also handle objects that are being used as maps", () => {
    const json = {
      messages: {
        "0": { from: "John", to: "Jane", subject: "Hello" },
        "1": { from: "Jane", to: "John", subject: "Hi" },
      },
    };
    const csv = jsonToCsv(json.messages);
    expect(csv).toEqual([
      ["from", "to", "subject"],
      ["John", "Jane", "Hello"],
      ["Jane", "John", "Hi"],
    ]);
  });
});

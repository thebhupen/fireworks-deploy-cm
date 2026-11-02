// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { JSONType } from "../components/JSONView";

export type CSV = Array<Array<string>>;

export function toStringCSV(Csv: CSV, delimiter = ",", newline = "\n"): string {
  return Csv.map((row) => {
    const escapedRow = row.map((element) =>
      element.includes(delimiter) || element.includes(newline)
        ? `"${element}"`
        : element,
    );

    return escapedRow.join(delimiter);
  }).join(newline);
}

export function jsonToCsv(json: JSONType): CSV {
  const table: CSV = [];
  const headers: Map<string, number> = new Map();
  let array = [];

  if (Array.isArray(json)) {
    array = json;
  } else if (typeof json === "object" && json != null) {
    array = Object.values(json);
  }

  for (const row of array) {
    const csvRow: Array<string> = [];

    for (const [key, maybeValue] of Object.entries(row)) {
      const value = maybeValue == null ? "" : maybeValue.toString();

      if (!headers.has(key)) {
        headers.set(key, headers.size);
      }

      const index = headers.get(key)!;

      if (index <= csvRow.length) {
        csvRow[index] = value;
      } else {
        while (csvRow.length < index) {
          csvRow.push("");
        }
        csvRow.push(value.toString());
      }
    }

    table.push(csvRow);
  }

  table.unshift(Array.from(headers.keys()));
  return table;
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { useCallback, useState } from "react";

import OnVisible from "./OnVisible";

import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton, Tooltip } from "@mui/material";
import "./JSONView.css";

const INDENTATION = 24;

export type JSONType =
  | ReadonlyArray<JSONType>
  | string
  | number
  | boolean
  | null
  | { [string: string]: JSONType };

type FlatJSON = Array<
  | {
      type: "void-array";
      key: string;
      indentation: number;
      childCount: number;
      path: string;
    }
  | {
      type: "void-object";
      key: string;
      indentation: number;
      childCount: number;
      path: string;
    }
  | {
      type: "object-start";
      key: string;
      indentation: number;
      childCount: number;
      path: string;
    }
  | {
      type: "object-end";
      indentation: number;
      path: string;
    }
  | {
      type: "array-start";
      key: string;
      indentation: number;
      childCount: number;
      path: string;
    }
  | {
      type: "array-end";
      indentation: number;
      path: string;
    }
  | {
      type: "value";
      key: string;
      value: string | number | boolean | null;
      indentation: number;
    }
>;

export function flattenJSON(
  json: JSONType,
  indentation: number = 0,
  path: string = "root",
  parentName: string = "",
): FlatJSON {
  const result: FlatJSON = [];

  switch (typeof json) {
    case "object": {
      if (json == null) {
        result.push({
          type: "value",
          key: parentName,
          value: null,
          indentation,
        });
        // If the array is larger than 10k items, it would cause a stack overflow, let's ignore it
      } else if (Array.isArray(json) && json.length > 10000) {
        result.push({
          type: "array-start",
          key: parentName,
          indentation,
          childCount: json.length,
          path,
        });

        result.push({
          type: "value",
          key: "0",
          value: `...${json.length} items`,
          indentation: indentation + 1,
        });

        result.push({
          type: "array-end",
          indentation,
          path,
        });
      } else if (Array.isArray(json)) {
        const children = json.flatMap((value, i) =>
          flattenJSON(
            value,
            indentation + 1,
            `${path}.${i.toString()}`,
            i.toString(),
          ),
        );

        result.push({
          type: "array-start",
          key: parentName,
          indentation,
          childCount: json.length,
          path,
        });

        result.push(...children);

        result.push({
          type: "array-end",
          indentation,
          path,
        });
      } else {
        const children = Object.entries(json).flatMap(([key, value]) =>
          flattenJSON(value, indentation + 1, `${path}.${key}`, key),
        );

        result.push({
          type: "object-start",
          key: parentName,
          indentation,
          childCount: Object.keys(json).length,
          path,
        });

        result.push(...children);

        result.push({
          type: "object-end",
          indentation,
          path,
        });
      }
      break;
    }
    case "boolean":
    case "number": {
      result.push({
        type: "value",
        key: parentName,
        value: json,
        indentation,
      });
      break;
    }
    case "string": {
      result.push({
        type: "value",
        key: parentName,
        value: json,
        indentation,
      });
      break;
    }
  }

  return result;
}

export default function JSONView({
  json,
  longTextWrap = false,
}: {
  json: JSONType;
  longTextWrap?: boolean;
}): React.ReactNode {
  const rows = flattenJSON(json, 0);
  const [visibleRows, setVisibleRows] = useState(100);
  const [folds, setFolds] = useState<{ [string: string]: boolean }>({});
  const isFolded = useCallback(
    (path: string) => {
      if (path.split(".").length <= 3) {
        return folds[path] === true;
      } else {
        return folds[path] === true || folds[path] === undefined;
      }
    },
    [folds],
  );

  const visibleItems: FlatJSON = [];

  for (let i = 0; i < rows.length; i++) {
    const item = rows[i];

    if (visibleItems.length >= visibleRows) {
      break;
    }

    switch (item.type) {
      case "object-start":
      case "array-start": {
        const path = item.path;

        if (item.childCount === 0 && item.type === "array-start") {
          visibleItems.push({ ...item, type: "void-array" });
          i++;
          continue;
        } else if (item.childCount === 0 && item.type === "object-start") {
          visibleItems.push({ ...item, type: "void-object" });
          i++;
          continue;
        }

        if (isFolded(path) === true) {
          visibleItems.push(item);

          while (i < rows.length) {
            const row = rows[++i];

            if (
              (row.type === "array-end" || row.type === "object-end") &&
              row.path === path
            ) {
              break;
            }
          }

          continue;
        }
        visibleItems.push(item);
        break;
      }
      default: {
        visibleItems.push(item);
        break;
      }
    }
  }

  const onVisible = useCallback(() => setVisibleRows((x) => x + 20), []);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        fontFamily: "monospace",
      }}
    >
      {visibleItems.map((item, index) => {
        switch (item.type) {
          case "object-start": {
            return (
              <JSONRow
                key={index}
                toggle={
                  <JSONToggle
                    collapsed={isFolded(item.path) === true}
                    onToggle={() => {
                      setFolds((folds) => ({
                        ...folds,
                        [item.path]: !isFolded(item.path),
                      }));
                    }}
                  />
                }
                indentation={item.indentation}
                name={item.key}
              >
                {isFolded(item.path) === true ? (
                  <JSONSpan
                    style={{ color: PRIMARY_COLOR }}
                  >{`{...},`}</JSONSpan>
                ) : (
                  <JSONSpan style={{ color: PRIMARY_COLOR }}>{`{`}</JSONSpan>
                )}
                <JSONSpan
                  style={{ color: SECONDARY_COLOR, marginLeft: INDENTATION }}
                >
                  {`${
                    item.childCount === 1
                      ? "1 item"
                      : `${item.childCount} items`
                  }`}
                </JSONSpan>
              </JSONRow>
            );
          }
          case "object-end": {
            return (
              <JSONRow key={index} indentation={item.indentation}>
                <JSONSpan style={{ color: PRIMARY_COLOR, marginLeft: 8 }}>
                  {item.indentation === 0 ? "}" : "},"}
                </JSONSpan>
              </JSONRow>
            );
          }
          case "void-array": {
            return (
              <JSONRow
                key={index}
                indentation={item.indentation}
                name={item.key}
              >
                <JSONSpan style={{ color: PRIMARY_COLOR }}>{`[],`}</JSONSpan>
              </JSONRow>
            );
          }
          case "void-object": {
            return (
              <JSONRow
                key={index}
                indentation={item.indentation}
                name={item.key}
              >
                <JSONSpan style={{ color: PRIMARY_COLOR }}>{`{},`}</JSONSpan>
              </JSONRow>
            );
          }
          case "array-start": {
            return (
              <JSONRow
                toggle={
                  <JSONToggle
                    collapsed={isFolded(item.path) === true}
                    onToggle={() => {
                      setFolds((folds) => ({
                        ...folds,
                        [item.path]: !isFolded(item.path),
                      }));
                    }}
                  />
                }
                key={index}
                indentation={item.indentation}
                name={item.key}
              >
                {isFolded(item.path) === true ? (
                  <JSONSpan
                    style={{ color: PRIMARY_COLOR }}
                  >{`[...],`}</JSONSpan>
                ) : (
                  <JSONSpan style={{ color: PRIMARY_COLOR }}>{`[`}</JSONSpan>
                )}
                <JSONSpan
                  style={{ color: SECONDARY_COLOR, marginLeft: INDENTATION }}
                >
                  {`${
                    item.childCount === 1
                      ? "1 item"
                      : `${item.childCount} items`
                  }`}
                </JSONSpan>
              </JSONRow>
            );
          }
          case "array-end": {
            return (
              <JSONRow key={index} indentation={item.indentation}>
                <JSONSpan
                  style={{ color: PRIMARY_COLOR, marginLeft: 8 }}
                >{`],`}</JSONSpan>
              </JSONRow>
            );
          }
          case "value": {
            const formattedValue =
              typeof item.value === "string"
                ? `"${item.value}",`
                : item.value === null
                  ? "null,"
                  : `${item.value},`;

            return (
              <JSONRow
                key={index}
                indentation={item.indentation}
                name={item.key}
                value={item.value}
              >
                <JSONSpan
                  style={{
                    color: VALUES_COLOR,
                    ...(longTextWrap
                      ? {
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-word",
                          overflow: "auto",
                          maxWidth: "100%",
                        }
                      : {
                          whiteSpace: "initial",
                          display: "-webkit-box",
                          WebkitLineClamp: 1,
                          WebkitBoxOrient: "vertical",
                          textOverflow: "ellipsis",
                          overflow: "hidden",
                        }),
                  }}
                >
                  {formattedValue}
                </JSONSpan>
              </JSONRow>
            );
          }
        }
      })}
      <OnVisible onVisible={onVisible} />
    </div>
  );
}

const SECONDARY_COLOR = "rgb(143, 161, 179)";
const PRIMARY_COLOR = "rgb(239, 241, 245)";
const VALUES_COLOR = "rgb(208, 135, 112)";
const HIGHLIGHT_COLOR = "rgb(180, 142, 173)";

function JSONToggle({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <button className="jsonview-toggle" onClick={() => onToggle()}>
      <JSONSpan
        style={{ color: collapsed ? HIGHLIGHT_COLOR : SECONDARY_COLOR }}
      >
        {collapsed ? "[+]" : "[-]"}
      </JSONSpan>
    </button>
  );
}

function JSONSpan({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: any;
}) {
  return (
    <span className={"jsonview-span"} style={style}>
      {children}
    </span>
  );
}

function JSONRow({
  children,
  name,
  indentation,
  toggle,
  value,
}: {
  children?: React.ReactNode;
  indentation: number;
  name?: string;
  toggle?: React.ReactNode;
  value?: string | number | boolean | null;
}) {
  const [copied, setCopied] = useState(false);

  return (
    <div
      className="jsonview-row"
      style={{
        marginLeft: indentation * INDENTATION,
      }}
    >
      {toggle}
      {value != null && (
        <Tooltip title={copied ? "Copied!" : "Copy value to clipboard"}>
          <div
            className="jsonview-row-copy"
            style={{
              position: "absolute",
              left: -24,
              zIndex: 1,
            }}
          >
            <IconButton
              size="small"
              onClick={() => {
                navigator.clipboard.writeText(value.toString());
                setCopied(true);
                setTimeout(() => setCopied(false), 1000);
              }}
            >
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </div>
        </Tooltip>
      )}
      {name && name !== "" && <JSONSpan>{`"${name}":\u00A0`}</JSONSpan>}
      {children}
      {Array(indentation)
        .fill(0)
        .map((_, i) => (
          <div
            key={i}
            className="jsonview-border"
            style={{
              left: -(i + 1) * INDENTATION + 11,
            }}
          />
        ))}
    </div>
  );
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { AgentLog } from "../../utils/types";

export function exportMarkdown({
  logs,
  filename,
  onSuccess,
  onError,
}: {
  logs: ReadonlyArray<AgentLog>;
  filename: string;
  onSuccess: () => void;
  onError: (error: Error) => void;
}): void {
  try {
    const markdown = asMarkdown({ logs, filename });
    downloadMarkdown({ markdown, filename });
    onSuccess();
  } catch (error: unknown) {
    if (error instanceof Error) {
      onError(error);
    }
  }
}

export function downloadMarkdown({
  markdown,
  filename,
}: {
  markdown: string;
  filename: string;
}): void {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([markdown], { type: "text/markdown" }));
  a.download = `${filename}.md`;
  a.click();
  a.remove();
}

export function asMarkdown({
  logs,
  filename,
}: {
  logs: ReadonlyArray<AgentLog>;
  filename: string;
}): string {
  const lines = [`# ${filename}`];

  for (const log of logs) {
    lines.push(`## ${log.type}`);
    lines.push(`* id: ${log.id}`);
    lines.push(`* timestamp: ${log.timestamp}`);

    if (log.groupId != null) {
      lines.push(`* groupId: ${log.groupId}`);
    }
    if (log.agent_name != null) {
      lines.push(`* agent_name: ${log.agent_name}`);
    }
    if (log.input != null) {
      lines.push(`* input: ${log.input}`);
    }
    if (log.output != null) {
      lines.push(`* output: ${log.output}`);
    }
    if (log.actionName != null) {
      lines.push(`* actionName: ${log.actionName}`);
    }
    if (log.appName != null) {
      lines.push(`* appName: ${log.appName}`);
    }
    if (log.exception != null) {
      lines.push(`* exception: ${log.exception}`);
    }
    if (log.exceptionStackTrace != null) {
      lines.push(`* exceptionStackTrace: ${log.exceptionStackTrace}`);
    }

    if (log.content != null) {
      lines.push(log.content);
    }
  }

  return lines.join("\n");
}

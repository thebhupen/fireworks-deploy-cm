// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Environment } from "react-relay";
import { fetchQuery, graphql } from "relay-runtime";
import type { TraceExporterQuery } from "./__generated__/TraceExporterQuery.graphql";
import { CapabilityTag } from "../../utils/types";

const downloadFile = (data: string, filename: string) => {
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

export const ExportQuery = graphql`
  query TraceExporterQuery(
    $sessionId: String!
    $scenarioId: String!
    $validationDecision: String
    $annotationId: String
    $annotatorName: String
    $comment: String
    $tags: [CapabilityTag!]
  ) {
    activeScenario(sessionId: $sessionId) {
      scenarioId
    }
    exportTraceData(
      sessionId: $sessionId
      scenarioId: $scenarioId
      validationDecision: $validationDecision
      annotationId: $annotationId
      annotatorName: $annotatorName
      comment: $comment
      tags: $tags
    )
  }
`;

export const runExport = ({
  environment,
  sessionId,
  scenarioId,
  validationDecision = null,
  annotationId = null,
  annotatorName = null,
  comment = null,
  tags = null,
  onError,
  onSuccess,
}: {
  environment: Environment;
  sessionId: string;
  scenarioId: string;
  validationDecision?: string | null;
  annotationId?: string | null;
  annotatorName?: string | null;
  comment?: string | null;
  tags?: CapabilityTag[] | null;
  onError: (error: Error) => void;
  onSuccess: () => void;
}) => {
  const variables = {
    sessionId: sessionId,
    scenarioId: scenarioId,
    validationDecision: validationDecision,
    annotationId: annotationId,
    annotatorName: annotatorName,
    comment: comment,
    tags: tags,
  };
  fetchQuery<TraceExporterQuery>(environment, ExportQuery, variables).subscribe(
    {
      next: (data) => {
        const jsonData = data.exportTraceData ?? "";
        const scenarioId = data?.activeScenario?.scenarioId;
        const filename = `${scenarioId}.json`;
        downloadFile(jsonData, filename);
      },
      error: (err: Error) => {
        console.error(err);
        onError(err);
      },
      complete: () => {
        onSuccess();
      },
    },
  );
};

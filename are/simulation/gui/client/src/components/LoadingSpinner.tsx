// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";
import { CircularProgress } from "@mui/material";
import { useInteractiveScenario } from "../hooks/useInteractiveScenario";

interface LoadingSpinnerProps {
  isLoading: boolean;
  loadingScenarioId: string | null | undefined;
  isResetting?: boolean;
}

function LoadingSpinner({
  isLoading,
  loadingScenarioId,
  isResetting = false,
}: LoadingSpinnerProps): React.ReactNode {
  const availableScenarios = useInteractiveScenario();

  if (!isLoading && !isResetting) {
    return null;
  }

  const scenarioLabel = loadingScenarioId
    ? availableScenarios[loadingScenarioId]?.label || loadingScenarioId
    : "...";

  const message = isResetting
    ? "Resetting scenario..."
    : `Loading scenario${loadingScenarioId ? `: ${scenarioLabel}` : "..."}`;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        zIndex: 9999,
        backdropFilter: "blur(2px)",
      }}
    >
      <CircularProgress size={60} sx={{ color: "white" }} />
      <div style={{ color: "white", marginTop: "20px", fontSize: "20px" }}>
        {message}
      </div>
    </div>
  );
}

export default LoadingSpinner;

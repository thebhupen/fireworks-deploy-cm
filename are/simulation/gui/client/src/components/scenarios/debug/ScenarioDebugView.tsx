// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { Stack, useTheme } from "@mui/material";
import { useReactFlow } from "@xyflow/react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import { ResizableBox } from "react-resizable";
import { useScenarioDebugContext } from "../../../contexts/ScenarioDebugContext";
import { FIT_VIEW_OPTIONS } from "../../dag/FlowDag";
import EventTimeline from "./events/EventTimeline";
import ScenarioLogs from "./ScenarioLogs";
import ValidateScenario from "./ValidateScenario";
import { ViewMode } from "./ViewModeToggle";

const MIN_HEIGHT = 400;
const MAX_HEIGHT = 800;

interface ScenarioDebugViewProps {
  hasMargin?: boolean;
}

/**
 * Scenario Debug View is a panel that lets users validate and debug by playing the scenario and viewing logs.
 */
const ScenarioDebugView = ({ hasMargin = true }: ScenarioDebugViewProps) => {
  const { isDebugViewOpen } = useScenarioDebugContext();
  const { fitView } = useReactFlow();
  const theme = useTheme();
  const [isResizing, setIsResizing] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Events);

  const handleViewModeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newViewMode: ViewMode | null,
  ) => {
    // Don't allow deselecting both options
    if (newViewMode !== null) {
      setViewMode(newViewMode);
    }
  };

  useEffect(() => {
    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        fitView(FIT_VIEW_OPTIONS);
      }
    };

    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  return (
    <AnimatePresence>
      {isDebugViewOpen && (
        <motion.div
          key="scenario-debug-view"
          style={{
            marginLeft: "8px",
            marginBottom: "8px",
            userSelect: isResizing ? "none" : "auto",
          }}
          initial={{ height: 0 }}
          animate={{
            height: "fit-content",
            marginTop: "8px",
            marginRight: hasMargin ? "8px" : "0px",
          }}
          exit={{ height: 0 }}
          transition={{
            type: "tween",
            duration: 0.2,
          }}
        >
          <ResizableBox
            width={Infinity}
            height={MIN_HEIGHT}
            minConstraints={[Infinity, MIN_HEIGHT]}
            maxConstraints={[Infinity, MAX_HEIGHT]}
            axis="y"
            resizeHandles={["n"]}
            onResizeStart={() => setIsResizing(true)}
            style={{ display: "flex" }}
            handle={
              <motion.span
                style={{
                  position: "absolute",
                  top: 0,
                  left: "50%",
                  transform: "translate(-50%, -150%)",
                  borderRadius: "2px",
                  cursor: "ns-resize",
                  width: "100%",
                  height: "4px",
                }}
                whileHover={{
                  backgroundColor: theme.palette.primary.main,
                  boxShadow: theme.shadows[3],
                }}
                whileDrag={{
                  backgroundColor: theme.palette.primary.main,
                  boxShadow: theme.shadows[3],
                }}
                animate={
                  isResizing
                    ? {
                        backgroundColor: theme.palette.primary.main,
                        boxShadow: theme.shadows[3],
                      }
                    : undefined
                }
              />
            }
          >
            <Stack direction="row" spacing={1} width={"100%"}>
              <ValidateScenario />
              <div
                style={{ width: "100%", height: "100%", overflow: "hidden" }}
              >
                <div
                  style={{
                    display: viewMode === ViewMode.Events ? "block" : "none",
                    width: "100%",
                    height: "100%",
                    overflow: "auto",
                  }}
                >
                  <EventTimeline
                    viewMode={viewMode}
                    onViewModeChange={handleViewModeChange}
                  />
                </div>
                <div
                  style={{
                    display: viewMode === ViewMode.Logs ? "block" : "none",
                    width: "100%",
                    height: "100%",
                    overflow: "auto",
                  }}
                >
                  <ScenarioLogs
                    viewMode={viewMode}
                    onViewModeChange={handleViewModeChange}
                  />
                </div>
              </div>
            </Stack>
          </ResizableBox>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ScenarioDebugView;

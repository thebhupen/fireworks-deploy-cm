// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CircleIcon from "@mui/icons-material/Circle";
import CodeIcon from "@mui/icons-material/Code";
import ForkRightIcon from "@mui/icons-material/ForkRight";
import PanToolIcon from "@mui/icons-material/PanTool";
import PersonIcon from "@mui/icons-material/Person";
import RuleIcon from "@mui/icons-material/Rule";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { AppName, ARESimulationEventType } from "../../../../utils/types.js";
import AppIcon from "../../../icons/AppIcon.js";

// Constants for styling
export const CONNECTOR_HEIGHT = 20;
export const CARD_WIDTH = 400;
export const NODE_AVATAR_BACKGROUND_COLOR = "#46494A";
const ICON_FONT_SIZE = 16;
const ICON_STYLE = { width: ICON_FONT_SIZE, height: ICON_FONT_SIZE };

// Helper function to get the appropriate icon for an event type
export const getIcon = (eventType: string, appName?: AppName) => {
  switch (eventType) {
    case ARESimulationEventType.Agent:
    case ARESimulationEventType.User:
    case ARESimulationEventType.Env:
      if (!appName) {
        return <CodeIcon sx={ICON_STYLE} />;
      }
      if (appName === "AgentUserInterface") {
        return eventType === ARESimulationEventType.Agent ? (
          <SmartToyIcon sx={ICON_STYLE} />
        ) : (
          <PersonIcon sx={ICON_STYLE} />
        );
      }
      return <AppIcon appName={appName} size={12} color="white" />;
    case ARESimulationEventType.Condition:
      return <ForkRightIcon sx={ICON_STYLE} />;
    case ARESimulationEventType.Validation:
      return <RuleIcon sx={ICON_STYLE} />;
    case ARESimulationEventType.Stop:
      return <PanToolIcon sx={ICON_STYLE} />;
    default:
      return <CircleIcon />;
  }
};

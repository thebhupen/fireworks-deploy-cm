// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import InfoOutline from "@mui/icons-material/InfoOutline";
import {
  Box,
  ButtonBase,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { ReactNode, useState } from "react";
import { ScenarioSource } from "../../hooks/useLoadScenario";
import HuggingFaceIcon from "../icons/HuggingFaceLogo";
import LoadIcon from "../icons/Load";
import LoadScenarioDialog from "../load-scenario/LoadScenarioDialog";

/**
 * ActionButton Component
 *
 * A reusable button component with a consistent style.
 * It accepts children and an onClick handler as props.
 */
interface ActionButtonProps {
  onClick: () => void;
  icon: ReactNode;
  label: string;
  tooltip: string;
}

const ActionButton = ({ onClick, icon, label, tooltip }: ActionButtonProps) => {
  const theme = useTheme();

  return (
    <Tooltip
      title={tooltip}
      placement="bottom"
      slotProps={{
        popper: {
          modifiers: [
            {
              name: "offset",
              options: {
                offset: [0, -14],
              },
            },
          ],
        },
      }}
    >
      <Stack
        alignItems={"center"}
        sx={{
          "&:hover": {
            "& .MuiButtonBase-root": {
              bgcolor: theme.palette.grey[800],
              borderColor: theme.palette.action.active,
              color: theme.palette.action.active,
            },
            "& .MuiButtonBase-root > *": {
              opacity: 1,
            },
            "& .MuiTypography-root": {
              color: theme.palette.action.active,
            },
          },
        }}
      >
        <ButtonBase
          onClick={onClick}
          sx={{
            borderRadius: 2,
            bgcolor: theme.palette.background.default,
            color: theme.palette.text.secondary,
            border: "2px dashed",
            borderColor: theme.palette.divider,
            height: 120,
            width: 120,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontSize: 60,
            transition: "all 0.2s ease-in-out",
            pointerEvents: "all",
          }}
        >
          <Box
            sx={{
              opacity: 0.5,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              transition: "all 0.2s ease-in-out",
            }}
          >
            {icon}
          </Box>
        </ButtonBase>
        <Typography
          color="text.disabled"
          sx={{
            maxWidth: 120,
            padding: 0.5,
            textWrap: "wrap",
            textAlign: "center",
            fontSize: 12,
            transition: "color 0.2s ease-in-out",
          }}
        >
          <span style={{ backgroundColor: theme.palette.background.default }}>
            {label}
          </span>
        </Typography>
      </Stack>
    </Tooltip>
  );
};

/**
 * GetStartedWithMessage Component
 *
 * This component displays a centered message encouraging users to add an event.
 * It shows instructional text and a button that triggers the createEvent function.
 * The component is typically shown when no events exist in the editor.
 */
const GetStartedWithMessage = () => {
  const theme = useTheme();
  const [isLoadScenarioDialogOpen, setIsLoadScenarioDialogOpen] =
    useState(false);
  const [scenarioSource, setScenarioSource] = useState<ScenarioSource>(
    ScenarioSource.Huggingface,
  );
  const loadScenario = (source: ScenarioSource) => {
    setScenarioSource(source);
    setIsLoadScenarioDialogOpen(true);
  };

  return (
    <>
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      >
        <Stack justifyContent={"center"} alignItems={"center"} spacing={6}>
          <Stack justifyContent={"center"} alignItems={"center"} spacing={0}>
            <Typography
              color="text.secondary"
              fontSize={24}
              textAlign={"center"}
              sx={{
                bgcolor: theme.palette.background.default,
                width: "fit-content",
              }}
            >
              Welcome to Meta Agents Research Environments
            </Typography>
            <Stack
              direction={"row"}
              spacing={1}
              justifyContent={"center"}
              alignItems={"center"}
              color="text.secondary"
            >
              <InfoOutline color="inherit" fontSize="small" />
              <Typography
                color="text.secondary"
                fontSize={"medium"}
                textAlign={"center"}
                sx={{
                  bgcolor: theme.palette.background.default,
                  width: "fit-content",
                }}
              >
                Current scenario has no scheduled events
              </Typography>
            </Stack>
          </Stack>
          <Stack direction={"row"} spacing={6}>
            <ActionButton
              icon={<HuggingFaceIcon size={38} />}
              label={"Load Gaia2 scenarios"}
              onClick={() => loadScenario(ScenarioSource.Huggingface)}
              tooltip="Load benchmark scenarios from Hugging Face "
            />
            <ActionButton
              icon={
                <LoadIcon
                  width={60}
                  height={60}
                  color={theme.palette.text.primary}
                />
              }
              label={"Load other scenarios"}
              onClick={() => loadScenario(ScenarioSource.Code)}
              tooltip="Load additional scenarios from code samples"
            />
          </Stack>
        </Stack>
        <LoadScenarioDialog
          isOpen={isLoadScenarioDialogOpen}
          onClose={() => setIsLoadScenarioDialogOpen(false)}
          defaultSource={scenarioSource}
        />
      </Box>
    </>
  );
};

export default GetStartedWithMessage;

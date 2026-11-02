// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

// @ts-ignore
import DeleteSweepIcon from "@mui/icons-material/DeleteSweep";
// @ts-ignore
import DataObjectIcon from "@mui/icons-material/DataObject";
// @ts-ignore
import DownloadingIcon from "@mui/icons-material/Downloading";
import ImageIcon from "@mui/icons-material/Image";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import TuneIcon from "@mui/icons-material/Tune";
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  FormControlLabel,
  Link,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Popper,
  Skeleton,
  Stack,
  Switch,
  // @ts-ignore
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { useReactFlow } from "@xyflow/react";
import { motion } from "motion/react";
import { useContext, useEffect, useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import { useScenarioDebugContext } from "../../contexts/ScenarioDebugContext";
import ScenarioExecutionContext from "../../contexts/ScenarioExecutionContext";
import SessionIdContext from "../../contexts/SessionIdContext";
import useRelayEnvironment from "../../relay/RelayEnvironment";
import { formatDateAndTimeFromTime } from "../../utils/TimeUtils";
import type { ARESimulationEvent } from "../../utils/types";
import { ARESimulationEventType } from "../../utils/types";
import { getUserPersonaFromApps } from "../../utils/UserPersonaUtils";
import useDownloadDag from "../dag/useDownloadDag";
import Import from "../icons/Load";
import { runExport } from "../import-export/TraceExporter";
import LoadScenarioDialog from "../load-scenario/LoadScenarioDialog";
import AgentSettingsDialog from "../settings/AgentSettingsDialog";
import UserPersonaDialog from "./UserPersonaDialog";
import UserPreferencesDialog from "./UserPreferencesDialog";

/**
 * ScenarioDetails component displays information about the current scenario and provides
 * controls for scenario management such as loading, saving, and debugging.
 *
 * @returns {JSX.Element} The rendered ScenarioDetails component
 */
const ScenariosHeader = () => {
  // Get scenario data and state from context
  const {
    appsState,
    initialEventQueue,
    scenario,
    reloadScenario,
    isLoadingScenario,
    userPreferences,
    // @ts-ignore
    userName,
  } = useAppContext();
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();
  const theme = useTheme();
  const { isDebugViewOpen, setIsDebugViewOpen } = useScenarioDebugContext();
  // @ts-ignore
  const isEditable = useContext(ScenarioExecutionContext).isEditable;
  const userPersona = getUserPersonaFromApps(appsState);

  // Dialog visibility states
  const [isLoadScenarioDialogOpen, setIsLoadScenarioDialogOpen] =
    useState(false);
  const [isUserPersonaDialogOpen, setIsUserPersonaDialogOpen] = useState(false);

  const [isUserPreferencesDialogOpen, setIsUserPreferencesDialogOpen] =
    useState(false);
  const [isAgentSettingsDialogOpen, setIsAgentSettingsDialogOpen] =
    useState(false);
  // @ts-ignore
  const [isDeleteAllEventsModalOpen, setIsDeleteAllEventsModalOpen] =
    useState(false);
  // @ts-ignore
  const [isSaveScenarioDialogOpen, setIsSaveScenarioDialogOpen] =
    useState(false);
  const [task, setTask] = useState<ARESimulationEvent | null>(null);
  const [taskAnchorEl, setTaskAnchorEl] = useState<HTMLButtonElement | null>(
    null,
  );

  // Clean up stale anchor element references
  useEffect(() => {
    if (taskAnchorEl && !document.contains(taskAnchorEl)) {
      setTaskAnchorEl(null);
    }
  }, [taskAnchorEl]);

  useEffect(() => {
    if (!initialEventQueue) {
      setTask(null);
      return;
    }
    try {
      const possibleTasks = initialEventQueue.filter(
        (ev) =>
          ev.event_type ===
            (ARESimulationEventType.User || ARESimulationEventType.Env) &&
          ev.dependencies.length === 0 &&
          ev.action.app_name === "AgentUserInterface" &&
          ev.action.function_name === "send_message_to_agent",
      );
      if (possibleTasks.length === 1) {
        setTask(possibleTasks[0]);
      } else {
        setTask(null);
      }
    } catch (err) {
      console.error(err);
      notify({ message: "Error: " + JSON.stringify(err), type: "error" });
    }
  }, [initialEventQueue]);

  // Menu state management
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const isMenuOpen = Boolean(menuAnchorEl);

  /**
   * Handles opening the menu by setting the anchor element
   * @param {React.MouseEvent<HTMLButtonElement>} event - The click event
   */
  const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };

  /**
   * Closes the menu by removing the anchor element
   */
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  // @ts-ignore
  const { setNodes } = useReactFlow();
  const { downloadDag: downloadPng, isDownloading: isDownloadingPng } =
    useDownloadDag();

  const isTaskPopperOpen = !!taskAnchorEl && document.contains(taskAnchorEl);

  let taskActionButton = null;
  let deleteAllEvents = null;
  let saveScenario = null;
  const dialogs = [
    <LoadScenarioDialog
      key="load-scenario-dialog"
      isOpen={isLoadScenarioDialogOpen}
      onClose={() => setIsLoadScenarioDialogOpen(false)}
    />,
    <UserPersonaDialog
      key="user-persona-dialog"
      isOpen={isUserPersonaDialogOpen}
      setIsOpen={setIsUserPersonaDialogOpen}
      userPersona={userPersona}
    />,
    <UserPreferencesDialog
      key="user-preferences-dialog"
      isOpen={isUserPreferencesDialogOpen}
      onClose={() => setIsUserPreferencesDialogOpen(false)}
    />,
    <AgentSettingsDialog
      key="agent-settings-dialog"
      isOpen={isAgentSettingsDialogOpen}
      onClose={() => setIsAgentSettingsDialogOpen(false)}
    />,
  ];

  return (
    <motion.div
      key="scenario-details"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{
        type: "tween",
        duration: 0.2,
      }}
    >
      <Stack
        direction="row"
        justifyContent={"space-between"}
        paddingX={3}
        paddingY={2}
        alignItems={"start"}
      >
        <Box>
          <Stack>
            {isLoadingScenario ? (
              <Skeleton
                variant="text"
                width={200}
                sx={{ fontSize: "1.35rem" }}
              />
            ) : (
              <Typography variant="h6">{scenario?.scenarioId}</Typography>
            )}
            {isLoadingScenario ? (
              <Skeleton
                variant="text"
                width={300}
                sx={{ fontSize: "1.2rem" }}
              />
            ) : (
              <Stack direction="row" spacing={1} alignItems={"center"}>
                <Typography
                  color="text.secondary"
                  display={"flex"}
                  alignItems={"center"}
                >
                  Persona:&nbsp;
                  {userPersona ? (
                    <>
                      <Link
                        onClick={() => setIsUserPersonaDialogOpen(true)}
                        underline="none"
                      >
                        {userPersona.first_name} {userPersona.last_name}
                      </Link>
                    </>
                  ) : (
                    "None"
                  )}
                </Typography>
                {scenario?.startTime ? (
                  <>
                    <Divider orientation="vertical" sx={{ height: "1rem" }} />
                    <Typography color="text.secondary">
                      Date:{" "}
                      {formatDateAndTimeFromTime(scenario.startTime * 1000)}
                    </Typography>
                  </>
                ) : null}
                {task && userPreferences.annotator.enhanceReadability && (
                  <>
                    <Divider orientation="vertical" sx={{ height: "1rem" }} />
                    <Box>
                      <Button
                        variant="text"
                        onClick={(e) => {
                          setTaskAnchorEl(
                            isTaskPopperOpen ? null : e.currentTarget,
                          );
                        }}
                      >
                        {isTaskPopperOpen ? "Hide Task" : "Show Task"}
                      </Button>
                      <Popper
                        anchorEl={taskAnchorEl}
                        placement="bottom"
                        open={isTaskPopperOpen}
                      >
                        <Box sx={{ maxWidth: "750px", position: "relative" }}>
                          <Card elevation={5}>
                            <CardContent>
                              {task.action.args.content}
                            </CardContent>
                          </Card>
                        </Box>
                      </Popper>
                    </Box>
                    {taskActionButton}
                  </>
                )}
              </Stack>
            )}
          </Stack>
        </Box>

        <Box display={"flex"} alignItems={"center"}>
          <Stack direction="row" spacing={3} alignItems={"center"}>
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={isDebugViewOpen}
                    onChange={(_, isChecked) => {
                      setIsDebugViewOpen(isChecked);
                    }}
                    disabled={!scenario || isLoadingScenario}
                  />
                }
                label="Execution panels"
              />
            </Stack>
            <Stack direction="row" spacing={0.5} alignItems={"center"}>
              <Button
                variant="outlined"
                color="white"
                startIcon={
                  <Import
                    color={
                      isLoadingScenario
                        ? theme.palette.text.disabled
                        : theme.palette.text.primary
                    }
                  />
                }
                onClick={() => setIsLoadScenarioDialogOpen(true)}
                disabled={isLoadingScenario}
              >
                Load scenario
              </Button>
              <Button
                variant="outlined"
                color="white"
                sx={{
                  minWidth: "32px",
                  width: "32px",
                }}
                onClick={handleMenuClick}
                disabled={isLoadingScenario}
              >
                <MoreHorizIcon />
              </Button>
              <Menu
                anchorEl={menuAnchorEl}
                open={isMenuOpen}
                onClose={handleMenuClose}
              >
                <MenuItem
                  onClick={() => {
                    setIsAgentSettingsDialogOpen(true);
                    handleMenuClose();
                  }}
                  disabled={isLoadingScenario}
                >
                  <ListItemIcon>
                    <SmartToyIcon htmlColor={theme.palette.text.secondary} />
                  </ListItemIcon>
                  <ListItemText>Select agent</ListItemText>
                </MenuItem>
                <Divider />
                {saveScenario}
                <MenuItem
                  onClick={() => {
                    downloadPng();
                    handleMenuClose();
                  }}
                  disabled={isLoadingScenario || isDownloadingPng}
                >
                  <ListItemIcon>
                    <ImageIcon htmlColor={theme.palette.text.secondary} />
                  </ListItemIcon>
                  <ListItemText>Quick save as PNG</ListItemText>
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleMenuClose();
                    runExport({
                      environment,
                      sessionId,
                      scenarioId: scenario?.scenarioId ?? "",
                      onSuccess: () => {
                        notify({
                          message: "Successfully downloaded scenario",
                          type: "success",
                        });
                      },
                      onError: (error) => {
                        notify({
                          message: `Failed to download scenario: ${error}`,
                          type: "error",
                        });
                      },
                    });
                  }}
                  disabled={isLoadingScenario}
                >
                  <ListItemIcon>
                    <DataObjectIcon fontSize="small" />
                  </ListItemIcon>
                  Quick save as JSON
                </MenuItem>
                <Divider />
                <MenuItem
                  onClick={() => {
                    reloadScenario();
                    handleMenuClose();
                    setIsDebugViewOpen(false);
                  }}
                  disabled={isLoadingScenario}
                >
                  <ListItemIcon>
                    <RestartAltIcon htmlColor={theme.palette.text.secondary} />
                  </ListItemIcon>
                  <ListItemText>Reload scenario</ListItemText>
                </MenuItem>
                {deleteAllEvents}
                <Divider />
                <MenuItem
                  onClick={() => {
                    setIsUserPreferencesDialogOpen(true);
                    handleMenuClose();
                  }}
                  disabled={isLoadingScenario}
                >
                  <ListItemIcon>
                    <TuneIcon htmlColor={theme.palette.text.secondary} />
                  </ListItemIcon>
                  <ListItemText>User preferences</ListItemText>
                </MenuItem>
              </Menu>
            </Stack>
          </Stack>
        </Box>
      </Stack>
      {dialogs}
    </motion.div>
  );
};

export default ScenariosHeader;

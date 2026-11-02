// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import DataObjectIcon from "@mui/icons-material/DataObject";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import TagIcon from "@mui/icons-material/Tag";
import CircularProgress from "@mui/material/CircularProgress";
import { useAppContext } from "../../contexts/AppContextProvider";
import { ScenarioSource } from "../../hooks/useLoadScenario";
import { useInteractiveScenario } from "../../hooks/useInteractiveScenario";

import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import {
  Button,
  FormControl,
  InputLabel,
  ListItemIcon,
  Menu,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { motion } from "motion/react";
import { ReactNode, useContext, useState } from "react";
import ReactDOM from "react-dom";
import ReactMarkdown from "react-markdown";
import { useRelayEnvironment } from "react-relay";
import { NO_AGENT_OPTION } from "../../constants/agentConstants";
import { useAgentConfigContext } from "../../contexts/AgentConfigContextProvider";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import ScenarioContext from "../../contexts/ScenarioContext";
import SessionIdContext from "../../contexts/SessionIdContext";
import commitSetAgent from "../../mutations/SetAgentNameMutation";
import { EnvState } from "../../utils/types";
import { runExport } from "../import-export/TraceExporter";
import { asMarkdown, exportMarkdown } from "./exportMarkdown";

interface PlaygroundChatHeaderProps {
  extraMenuItems?: ReactNode[];
}

export function PlaygroundChatHeader({
  extraMenuItems,
}: PlaygroundChatHeaderProps) {
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const { scenarioId } = useContext(ScenarioContext);
  const { envState, worldLogs, isLoadingScenario, loadScenario } =
    useAppContext();
  const [printing, setPrinting] = useState(false);
  const { notify } = useNotifications();
  const isRunning = envState === EnvState.RUNNING || isLoadingScenario;
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { agent, setAgent, agents, setAgentConfig } = useAgentConfigContext();

  // Use the hook to get available scenarios
  const availableScenarios = useInteractiveScenario();
  const interactiveScenarios = Object.values(availableScenarios);

  let agentSelectTooltipTitle = "Agent change not yet supported";
  let universeSelectTooltipTitle = "Universe change not yet supported";
  let isSelectionDisabled = true;
  let clipboardLink = null;

  const setSelectedScenario = (scenario: string) => {
    try {
      loadScenario(ScenarioSource.Code, { scenarioId: scenario });
    } catch (err) {
      console.error(err);
      notify({ message: "Error: " + JSON.stringify(err), type: "error" });
    }
  };

  const handleAgentSelect = (agent: string) => {
    const selectedAgent: string | null =
      agent === NO_AGENT_OPTION ? null : agent;
    setAgent(selectedAgent);
    commitSetAgent(environment, selectedAgent, sessionId, notify, (response) =>
      setAgentConfig(response),
    );
  };

  return (
    <motion.div
      key="agent-chat-header"
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
        <Typography variant="h6">Agent chat</Typography>
        <Stack direction="row" spacing={0.5} alignItems="center">
          {clipboardLink}
          <Tooltip title={agentSelectTooltipTitle}>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel id="agent-select-label">Agent</InputLabel>
              <Select
                labelId="agent-select-label"
                id="agent-select"
                value={agent ?? NO_AGENT_OPTION}
                label="Agent"
                onChange={(event) => {
                  handleAgentSelect(event.target.value as string);
                }}
                disabled={isSelectionDisabled || isRunning}
                autoWidth
              >
                {[NO_AGENT_OPTION, ...agents].map((agent) => (
                  <MenuItem key={agent} value={agent}>
                    {agent}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Tooltip>
          <Tooltip title={universeSelectTooltipTitle}>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel id="scenario-select-universe-label">
                Universe
              </InputLabel>
              <Select
                labelId="scenario-select-universe-label"
                id="scenario-select"
                value={scenarioId ?? ""}
                label="Universe"
                onChange={(event) => {
                  setSelectedScenario(event.target.value as string);
                }}
                disabled={isSelectionDisabled || isRunning}
                autoWidth
                startAdornment={
                  isLoadingScenario ? (
                    <CircularProgress size={20} sx={{ marginRight: 1 }} />
                  ) : null
                }
              >
                {scenarioId &&
                  !interactiveScenarios.some((s) => s["id"] === scenarioId) && (
                    <MenuItem key={scenarioId} value={scenarioId}>
                      {scenarioId}
                    </MenuItem>
                  )}
                {interactiveScenarios.map(({ id, label }) => (
                  <MenuItem key={id} value={id}>
                    {label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Tooltip>
          <Button
            variant="outlined"
            color="white"
            size="large"
            sx={{
              minWidth: "36px",
              height: "36px",
              padding: 1,
            }}
            onClick={(event) => {
              if (event.target != null) {
                setAnchorEl(event.currentTarget);
              }
            }}
            disabled={isLoadingScenario}
          >
            <MoreHorizIcon />
          </Button>
          {printing && (
            <Printable>
              <ReactMarkdown>
                {asMarkdown({
                  logs: worldLogs,
                  filename: scenarioId ?? "scenario",
                })}
              </ReactMarkdown>
            </Printable>
          )}
          <Menu
            anchorEl={anchorEl}
            onClose={() => {
              setAnchorEl(null);
            }}
            open={anchorEl != null}
          >
            {extraMenuItems}
            <MenuItem
              onClick={() => {
                setAnchorEl(null);
                runExport({
                  environment,
                  sessionId,
                  scenarioId: scenarioId ?? "",
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
            >
              <ListItemIcon>
                <DataObjectIcon fontSize="small" />
              </ListItemIcon>
              Save trace as JSON
            </MenuItem>
            <MenuItem
              onClick={() => {
                setAnchorEl(null);
                exportMarkdown({
                  logs: worldLogs,
                  filename: scenarioId ?? "scenario",
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
            >
              <ListItemIcon>
                <TagIcon fontSize="small" />
              </ListItemIcon>
              Save trace as Markdown
            </MenuItem>
            <MenuItem
              onClick={() => {
                setPrinting(true);
                setAnchorEl(null);
                // We need to wait for the menu to close before printing, or it would show in the printed document
                queueMicrotask(() => {
                  window.print();
                });
              }}
            >
              <ListItemIcon>
                <PictureAsPdfIcon fontSize="small" />
              </ListItemIcon>
              Save trace as PDF
            </MenuItem>
          </Menu>
        </Stack>
      </Stack>
    </motion.div>
  );
}

function Printable({ children }: { children: ReactNode }) {
  const printable = document.getElementById("printable");
  return printable && ReactDOM.createPortal(children, printable);
}

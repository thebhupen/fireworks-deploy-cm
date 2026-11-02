// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import ArchitectureIcon from "@mui/icons-material/Architecture";
import BuildIcon from "@mui/icons-material/Build";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import CodeIcon from "@mui/icons-material/Code";
import DoNotDisturbIcon from "@mui/icons-material/DoNotDisturb";
import EditIcon from "@mui/icons-material/Edit";
import EmojiObjectsIcon from "@mui/icons-material/EmojiObjects";
import ErrorIcon from "@mui/icons-material/Error";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import FlagIcon from "@mui/icons-material/Flag";
import InputIcon from "@mui/icons-material/Input";
import ManageSearchIcon from "@mui/icons-material/ManageSearch";
import MapIcon from "@mui/icons-material/Map";
import NotesIcon from "@mui/icons-material/Notes";
import OutputIcon from "@mui/icons-material/Output";
import PsychologyIcon from "@mui/icons-material/Psychology";
import QuestionMarkIcon from "@mui/icons-material/QuestionMark";
import StairsIcon from "@mui/icons-material/Stairs";
import TaskIcon from "@mui/icons-material/Task";
import TerminalIcon from "@mui/icons-material/Terminal";
import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  alpha,
  Box,
  Checkbox,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { motion } from "motion/react";
import React, { useState } from "react";
import { AgentLog, AgentLogType, isEditableLog } from "../../utils/types";
import { AgentLogDetailView } from "./AgentLogDetailView";

type AgentLogWithIndex = {
  type: "log";
  index: number;
  log: AgentLog;
};
type AgentLogGroup = {
  type: "group";
  logs: Array<AgentLogWithIndex | AgentLogGroup>;
  name: string;
};
function groupAgentLogs(
  worldLogs: ReadonlyArray<AgentLog>,
): Array<AgentLogGroup> {
  const result: Array<AgentLogGroup> = [];
  const groupStack: Array<{ group: AgentLogGroup; groupId: string }> = [];

  const rootGroup = createNewGroup("ROOT");
  result.push(rootGroup);
  groupStack.push({ group: rootGroup, groupId: "" });

  for (let i = 0; i < worldLogs.length; i++) {
    const log = worldLogs[i];

    if (log.type === "STEP" || log.type === "SUBAGENT") {
      const groupName = log.content || "GROUP";
      const newGroup = createNewGroup(groupName);

      const parentIndex = findParentGroupIndex(groupStack, log.groupId || "");
      if (parentIndex !== -1) {
        groupStack[parentIndex].group.logs.push(newGroup);
        groupStack.splice(parentIndex + 1);
      } else {
        result.push(newGroup);
      }

      groupStack.push({ group: newGroup, groupId: log.id });
    } else {
      const parentIndex = findParentGroupIndex(groupStack, log.groupId || "");
      if (parentIndex !== -1) {
        groupStack[parentIndex].group.logs.push({
          log: worldLogs[i],
          index: i,
          type: "log",
        });
      } else {
        rootGroup.logs.push({
          log: worldLogs[i],
          index: i,
          type: "log",
        });
      }
    }
  }

  return result;
}

function findParentGroupIndex(
  groupStack: Array<{ group: AgentLogGroup; groupId: string }>,
  groupId: string,
): number {
  for (let j = groupStack.length - 1; j >= 0; j--) {
    if (groupStack[j].groupId === groupId) {
      return j;
    }
  }
  return -1;
}

function createNewGroup(name: string): AgentLogGroup {
  return {
    type: "group",
    name,
    logs: [],
  };
}

type VisibilityMap = {
  [key in AgentLogType]: boolean | "hidden";
};

export function AgentLogsSection({
  worldLogs,
  showHeader = true,
}: {
  worldLogs: ReadonlyArray<AgentLog>;
  showHeader?: boolean;
}) {
  const [unsafeSelectedLogIndex, setSelectedLogIndex] = useState<number | null>(
    null,
  );

  const [visibilityMap, setVisibilityMap] = React.useState<VisibilityMap>({
    SYSTEM_PROMPT: true,
    TASK: true,
    LLM_INPUT: true,
    LLM_OUTPUT_THOUGHT_ACTION: true,
    RATIONALE: true,
    TOOL_CALL: true,
    OBSERVATION: true,
    STEP: "hidden",
    FINAL_ANSWER: true,
    ERROR: true,
    THOUGHT: true,
    PLAN: true,
    FACTS: true,
    REPLAN: true,
    REFACTS: true,
    AGENT_STOP: true,
    CODE_EXECUTION_RESULT: true,
    CODE_STATE_UPDATE: true,
    END_TASK: true,
    LLM_OUTPUT_PLAN: true,
    LLM_OUTPUT_FACTS: true,
    SUBAGENT: "hidden",
  });

  const selectedLogIndex =
    unsafeSelectedLogIndex !== null && unsafeSelectedLogIndex < worldLogs.length
      ? unsafeSelectedLogIndex
      : null;
  const selectedLog =
    selectedLogIndex !== null ? worldLogs[selectedLogIndex] : null;
  const groupedAgentLogs = groupAgentLogs(worldLogs);
  const theme = useTheme();

  return (
    <Stack direction="column" sx={{ flex: 1, height: "100%" }}>
      {showHeader && (
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
            <Typography variant="h6">Agent logs</Typography>
            <AgentLogsFilters
              visibilityMap={visibilityMap}
              setVisibilityMap={setVisibilityMap}
              worldLogs={worldLogs}
            />
          </Stack>
        </motion.div>
      )}
      {worldLogs.length === 0 ? (
        <Stack
          width={"100%"}
          height={"100%"}
          justifyContent={"center"}
          alignItems={"center"}
          spacing={1}
        >
          <ManageSearchIcon
            htmlColor={theme.palette.text.disabled}
            fontSize="large"
          />
          <Typography color="text.disabled">No logs</Typography>
        </Stack>
      ) : (
        <Stack
          direction="row"
          gap={1}
          sx={{
            padding: 1,
            flexGrow: 1,
            overflow: "hidden",
            height: "100%",
          }}
        >
          <Box
            sx={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              overflowY: "auto",
              overflowX: "hidden",
              gap: 0,
              flexGrow: 0,
              flexShrink: 0,
              minWidth: "20%",
              maxWidth: "50%",
            }}
          >
            {groupedAgentLogs.map((group, groupIndex) => {
              return (
                <AgentGroupToggle
                  visibilityMap={visibilityMap}
                  key={groupIndex}
                  group={group}
                  selectedLogIndex={selectedLogIndex}
                  setSelectedLogIndex={setSelectedLogIndex}
                  name={group.name}
                  initialExpanded={true}
                />
              );
            })}
          </Box>
          {selectedLog ? (
            <AgentLogDetailView log={selectedLog} />
          ) : (
            <Typography
              sx={{ color: theme.palette.text.secondary, padding: 2 }}
            >
              Select a log to view details.
            </Typography>
          )}
        </Stack>
      )}
    </Stack>
  );
}

function AgentLogsFilters({
  visibilityMap,
  setVisibilityMap,
  worldLogs,
}: {
  visibilityMap: { [key in AgentLogType]: boolean | "hidden" };
  setVisibilityMap: React.Dispatch<
    React.SetStateAction<{
      [key in AgentLogType]: boolean | "hidden";
    }>
  >;
  worldLogs: ReadonlyArray<AgentLog>;
}) {
  const countMap: { [key in AgentLogType]: number } = {
    SYSTEM_PROMPT: 0,
    TASK: 0,
    LLM_INPUT: 0,
    LLM_OUTPUT_THOUGHT_ACTION: 0,
    RATIONALE: 0,
    TOOL_CALL: 0,
    OBSERVATION: 0,
    STEP: 0,
    FINAL_ANSWER: 0,
    ERROR: 0,
    THOUGHT: 0,
    PLAN: 0,
    FACTS: 0,
    REPLAN: 0,
    REFACTS: 0,
    AGENT_STOP: 0,
    CODE_EXECUTION_RESULT: 0,
    CODE_STATE_UPDATE: 0,
    END_TASK: 0,
    LLM_OUTPUT_PLAN: 0,
    LLM_OUTPUT_FACTS: 0,
    SUBAGENT: 0,
  };

  for (const log of worldLogs) {
    countMap[log.type] += 1;
  }

  const visibleLogTypes = Object.entries(visibilityMap)
    .filter(
      ([type, value]) =>
        value !== "hidden" && countMap[type as AgentLogType] > 0,
    )
    .map(([type]) => type as AgentLogType);

  const selectedLogTypes = visibleLogTypes.filter(
    (type) => visibilityMap[type] === true,
  );

  const handleChange = (event: SelectChangeEvent<AgentLogType[]>) => {
    const selectedTypes = event.target.value as AgentLogType[];
    const newVisibilityMap = { ...visibilityMap };

    visibleLogTypes.forEach((type) => {
      newVisibilityMap[type] = false;
    });

    selectedTypes.forEach((type) => {
      newVisibilityMap[type] = true;
    });

    setVisibilityMap(newVisibilityMap);
  };

  return (
    <FormControl
      size="small"
      sx={{ width: 300 }}
      disabled={worldLogs.length === 0}
    >
      <InputLabel id="log-type-select-label">Log types</InputLabel>
      <Select
        labelId="log-type-select-label"
        id="log-type-select"
        multiple
        value={selectedLogTypes}
        onChange={handleChange}
        label="Log Types"
        renderValue={(selected) => `${selected.length} types selected`}
        autoWidth
      >
        {visibleLogTypes.map((type) => (
          <MenuItem key={type} value={type} dense>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <Checkbox size="small" checked={visibilityMap[type] === true} />
              {getLogIcon(type)}
              <Typography>{`${type} (${countMap[type]})`}</Typography>
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

function AgentGroupToggle({
  visibilityMap,
  group,
  name,
  setSelectedLogIndex,
  selectedLogIndex,
  initialExpanded = true,
}: {
  visibilityMap: { [key in AgentLogType]: boolean | "hidden" };
  group: AgentLogGroup;
  name: string;
  setSelectedLogIndex: (index: number) => void;
  selectedLogIndex: number | null;
  initialExpanded?: boolean;
}) {
  const [isExpanded, setIsExpanded] = React.useState(initialExpanded);
  const theme = useTheme();

  if (group.logs.length === 0) {
    return null;
  }

  const children = group.logs.map((log, index) => {
    if (log.type === "log") {
      if (!visibilityMap[log.log.type]) {
        return null;
      }

      return (
        <AgentLogElement
          key={index}
          log={log.log}
          index={log.index}
          selectedLogIndex={selectedLogIndex}
          setSelectedLogIndex={setSelectedLogIndex}
        />
      );
    } else {
      return (
        <AgentGroupToggle
          visibilityMap={visibilityMap}
          key={index}
          group={log}
          name={log.name}
          setSelectedLogIndex={setSelectedLogIndex}
          selectedLogIndex={selectedLogIndex}
        />
      );
    }
  });

  return (
    <>
      <Box
        role="button"
        sx={{
          display: "flex",
          gap: 0,
          position: "relative",
          padding: 0.5,
          borderRadius: "4px",
          cursor: "pointer",
          "&:hover": {
            backgroundColor: alpha(theme.palette.primary.main, 0.12),
          },
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <ChevronRightIcon
          sx={{
            transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease-in-out",
            color: theme.palette.primary.main,
          }}
        />
        <Typography sx={{ color: theme.palette.text.primary }}>
          {name}
        </Typography>
      </Box>
      {isExpanded && (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0,
            position: "relative",
            paddingLeft: "32px",
          }}
        >
          <Box
            sx={{
              position: "absolute",
              top: 0,
              left: 14,
              width: "1px",
              bottom: 0,
              backgroundColor: alpha(theme.palette.primary.main, 0.2),
            }}
          />
          {children}
        </Box>
      )}
    </>
  );
}

function AgentLogElement({
  setSelectedLogIndex,
  index,
  selectedLogIndex,
  log,
}: {
  setSelectedLogIndex: (index: number) => void;
  index: number;
  selectedLogIndex: number | null;
  log: AgentLog;
}) {
  const theme = useTheme();
  const isEditable = isEditableLog(log);

  return (
    <Stack
      direction="row"
      gap={1}
      onClick={() => setSelectedLogIndex(index)}
      sx={{
        padding: 0.5,
        borderRadius: "4px",
        cursor: "pointer",
        "&:hover": {
          backgroundColor: alpha(theme.palette.secondary.main, 0.12),
        },
        backgroundColor:
          selectedLogIndex === index
            ? alpha(theme.palette.secondary.main, 0.12)
            : "transparent",
        color: theme.palette.text.secondary,
      }}
    >
      {getLogIcon(log.type)}
      {log.type}
      {isEditable ? (
        <Tooltip title="This log is editable">
          <EditIcon
            fontSize="small"
            sx={{ color: alpha(theme.palette.text.secondary, 0.4) }}
          />
        </Tooltip>
      ) : null}
    </Stack>
  );
}

function getLogIcon(type: AgentLogType) {
  if (type === "SYSTEM_PROMPT") {
    return <TerminalIcon />;
  } else if (type === "TASK") {
    return <TaskIcon />;
  } else if (type === "LLM_INPUT") {
    return <InputIcon />;
  } else if (type === "LLM_OUTPUT_THOUGHT_ACTION") {
    return <OutputIcon />;
  } else if (type === "RATIONALE") {
    return <EmojiObjectsIcon />;
  } else if (type === "TOOL_CALL") {
    return <BuildIcon />;
  } else if (type === "OBSERVATION") {
    return <VisibilityIcon />;
  } else if (type === "STEP") {
    return <StairsIcon />;
  } else if (type === "FINAL_ANSWER") {
    return <FlagIcon />;
  } else if (type === "ERROR") {
    return <ErrorIcon />;
  } else if (type === "THOUGHT") {
    return <PsychologyIcon />;
  } else if (type === "PLAN") {
    return <MapIcon />;
  } else if (type === "FACTS") {
    return <FactCheckIcon />;
  } else if (type === "REPLAN") {
    return <ArchitectureIcon />;
  } else if (type === "REFACTS") {
    return <ArchitectureIcon />;
  } else if (type === "AGENT_STOP") {
    return <DoNotDisturbIcon />;
  } else if (type === "LLM_OUTPUT_FACTS" || type === "LLM_OUTPUT_PLAN") {
    return <NotesIcon />;
  } else if (type === "CODE_STATE_UPDATE" || type === "CODE_EXECUTION_RESULT") {
    return <CodeIcon />;
  } else {
    console.warn("Unknown log type", type);
    return <QuestionMarkIcon />;
  }
}

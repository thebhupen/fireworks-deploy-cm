// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  MenuItem,
  Select,
  Stack,
} from "@mui/material";
import * as React from "react";
import { useContext, useState } from "react";
import { useMutation } from "react-relay";
import { useAgentConfigContext } from "../../contexts/AgentConfigContextProvider";
import { useAppContext } from "../../contexts/AppContextProvider";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import ScenarioExecutionContext from "../../contexts/ScenarioExecutionContext";
import SessionIdContext from "../../contexts/SessionIdContext";
import type { SetAgentNameMutation as SetAgentNameMutationType } from "../../mutations/__generated__/SetAgentNameMutation.graphql";
import { SetAgentNameMutation } from "../../mutations/SetAgentNameMutation";
import { NO_AGENT_OPTION } from "../../constants/agentConstants";
import FormInputLabel from "../common/inputs/FormInputLabel";

interface AgentSettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

function AgentSettingsDialog({
  isOpen,
  onClose,
}: AgentSettingsDialogProps): React.ReactNode {
  const sessionId = useContext<string>(SessionIdContext);
  const { notify } = useNotifications();
  const { isLoadingScenario } = useAppContext();
  const { isRunning } = useContext(ScenarioExecutionContext);

  const { agent, setAgent, agents } = useAgentConfigContext();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(agent);

  const [commitSetAgent, isInFlight] =
    useMutation<SetAgentNameMutationType>(SetAgentNameMutation);

  const handleAgentSelect = (agentName: string) => {
    const selected = agentName === NO_AGENT_OPTION ? null : agentName;
    setSelectedAgent(selected);
  };

  const handleSave = () => {
    commitSetAgent({
      variables: {
        agentId: selectedAgent,
        sessionId,
      },
      onCompleted: (_, errors) => {
        if (errors) {
          console.log("Errors:", errors);
          notify({
            message: "Errors: " + JSON.stringify(errors),
            type: "error",
          });
        } else {
          setAgent(selectedAgent);
          notify({
            message: `Agent set to ${selectedAgent ?? NO_AGENT_OPTION}`,
            type: "success",
          });
          onClose();
        }
      },
      onError: (err) => {
        console.error(err);
        notify({
          message: "Error: " + JSON.stringify(err),
          type: "error",
        });
      },
    });
  };

  return (
    <Dialog open={isOpen} onClose={onClose} fullWidth>
      <DialogTitle>Select agent</DialogTitle>
      <DialogContent>
        <FormControl fullWidth>
          <FormInputLabel label="Agent" />
          <Select
            value={selectedAgent ?? NO_AGENT_OPTION}
            onChange={(e) => handleAgentSelect(e.target.value!)}
            disabled={isRunning || isLoadingScenario || isInFlight}
          >
            {[NO_AGENT_OPTION, ...agents].map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Stack spacing={1} direction="row" justifyContent="flex-end">
          <Button onClick={onClose} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isRunning || isLoadingScenario || isInFlight}
            variant="contained"
          >
            Save
          </Button>
        </Stack>
      </DialogActions>
    </Dialog>
  );
}

export default AgentSettingsDialog;

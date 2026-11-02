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
} from "@mui/material";
import * as React from "react";
import { useContext } from "react";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../contexts/SessionIdContext";
import commitDeleteScenarioEvent from "../../mutations/DeleteScenarioEventMutation";
import useRelayEnvironment from "../../relay/RelayEnvironment";

const DeleteEvent = ({
  event,
  isOpen,
  onClose,
}: {
  event: any;
  isOpen: boolean;
  onClose: () => void;
}): React.ReactNode | null => {
  const sessionId = useContext(SessionIdContext);
  const environment = useRelayEnvironment();
  const { notify } = useNotifications();

  const handleConfirm = () => {
    commitDeleteScenarioEvent(environment, sessionId, event?.event_id, notify);
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogTitle>Delete this event?</DialogTitle>
      <DialogContent>
        Only this event will be deleted. You can link the downstream events to
        other events by using the edit button.
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleConfirm} color="error" variant="contained">
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};
export default DeleteEvent;

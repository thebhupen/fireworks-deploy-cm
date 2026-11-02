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
  FormHelperText,
  TextField,
} from "@mui/material";
import { useContext, useState, useEffect } from "react";
import { useMutation } from "react-relay";
import { useNotifications } from "../../contexts/NotificationsContextProvider";
import SessionIdContext from "../../contexts/SessionIdContext";
import { EditScenarioDurationMutation } from "../../mutations/EditScenarioDurationMutation";

interface DurationDialogProps {
  duration: number | null;
  setDuration: (duration: number | null) => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const DIALOG_WIDTH = "300px";

const DurationDialog = ({
  isOpen,
  setIsOpen,
  duration,
  setDuration,
}: DurationDialogProps) => {
  const sessionId = useContext(SessionIdContext);
  const [newDuration, setNewDuration] = useState<string | null>(`${duration}`);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [commitEditScenarioDuration, isEditScenarioDurationInFlight] =
    useMutation(EditScenarioDurationMutation);
  const { notify } = useNotifications();

  const validateDuration = (input: number) => {
    if (input === null || !Number.isInteger(input) || input < 0) {
      setValidationError(
        "Duration must be an integer greater than or equal to 0",
      );
    } else {
      setValidationError(null);
    }
  };

  const handleDurationChange = () => {
    if (!newDuration || validationError) {
      return;
    }
    commitEditScenarioDuration({
      variables: {
        sessionId,
        duration: +newDuration,
      },
      onCompleted: (_, errors) => {
        if (errors && errors.length > 0) {
          notify({
            type: "error",
            message: `Failed to edit scenario duration: ${errors[0].message}`,
          });
        } else {
          setDuration(+newDuration);
          setIsOpen(false);
        }
      },
      onError: (error) => {
        notify({
          type: "error",
          message: `Failed to edit scenario duration: ${error.message}`,
        });
      },
    });
  };

  useEffect(() => {
    setNewDuration(`${duration}`);
  }, [duration]);

  return (
    <Dialog
      open={isOpen}
      onClose={() => {
        if (!isEditScenarioDurationInFlight) {
          setIsOpen(false);
        }
      }}
    >
      <DialogTitle>Set Duration</DialogTitle>
      <DialogContent sx={{ width: DIALOG_WIDTH }}>
        <FormControl size="small" variant="outlined" error={!!validationError}>
          <TextField
            size="small"
            type="number"
            value={newDuration}
            placeholder="Duration"
            onChange={(e) => {
              validateDuration(+e.target.value);
              setNewDuration(e.target.value);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !validationError && newDuration !== "") {
                handleDurationChange();
              }
            }}
          />
          <FormHelperText>
            {validationError ??
              "Total duration to run the scenario for in seconds. Enter 0 for no limit."}
          </FormHelperText>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={() => {
            setIsOpen(false);
            setNewDuration(`${duration}`);
          }}
          disabled={isEditScenarioDurationInFlight}
        >
          Cancel
        </Button>
        <Button
          onClick={handleDurationChange}
          disabled={!!validationError || newDuration === ""}
          variant="contained"
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DurationDialog;

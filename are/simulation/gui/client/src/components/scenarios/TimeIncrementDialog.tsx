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
import { EditTimeIncrementMutation } from "../../mutations/EditTimeIncrementMutation";

interface TimeIncrementDialogProps {
  timeIncrement: number | null;
  setTimeIncrement: (timeIncrement: number | null) => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const DIALOG_WIDTH = "300px";

const TimeIncrementDialog = ({
  isOpen,
  setIsOpen,
  timeIncrement,
  setTimeIncrement,
}: TimeIncrementDialogProps) => {
  const sessionId = useContext(SessionIdContext);
  const [newTimeIncrement, setNewTimeIncrement] = useState<string | null>(
    `${timeIncrement}`,
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  const [commitEditTimeIncrement, isEditTimeIncrementInFlight] = useMutation(
    EditTimeIncrementMutation,
  );
  const { notify } = useNotifications();

  const validateTimeIncrement = (input: number) => {
    if (input === null || !Number.isInteger(input) || input < 1) {
      setValidationError(
        "Time increment must be an integer greater than or equal to 1",
      );
    } else {
      setValidationError(null);
    }
  };

  const handleTimeIncrementChange = () => {
    if (!newTimeIncrement || validationError) {
      return;
    }
    commitEditTimeIncrement({
      variables: {
        sessionId,
        duration: null,
        timeIncrement: +newTimeIncrement,
      },
      onCompleted: (_, errors) => {
        if (errors && errors.length > 0) {
          notify({
            type: "error",
            message: `Failed to edit time increment: ${errors[0].message}`,
          });
        } else {
          setTimeIncrement(+newTimeIncrement);
          setIsOpen(false);
        }
      },
      onError: (error) => {
        notify({
          type: "error",
          message: `Failed to edit time increment: ${error.message}`,
        });
      },
    });
  };

  useEffect(() => {
    setNewTimeIncrement(`${timeIncrement}`);
  }, [timeIncrement]);

  return (
    <Dialog
      open={isOpen}
      onClose={() => {
        if (!isEditTimeIncrementInFlight) {
          setIsOpen(false);
        }
      }}
    >
      <DialogTitle>Set Time Increment</DialogTitle>
      <DialogContent sx={{ width: DIALOG_WIDTH }}>
        <FormControl size="small" variant="outlined" error={!!validationError}>
          <TextField
            size="small"
            type="number"
            value={newTimeIncrement}
            placeholder="Time increment"
            onChange={(e) => {
              validateTimeIncrement(+e.target.value);
              setNewTimeIncrement(e.target.value);
            }}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !validationError &&
                newTimeIncrement !== ""
              ) {
                handleTimeIncrementChange();
              }
            }}
          />
          <FormHelperText>
            {validationError ??
              "Time increment in seconds between each tick. Use 1 for real time."}
          </FormHelperText>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={() => {
            setIsOpen(false);
            setNewTimeIncrement(`${timeIncrement}`);
          }}
          disabled={isEditTimeIncrementInFlight}
        >
          Cancel
        </Button>
        <Button
          onClick={handleTimeIncrementChange}
          disabled={!!validationError || newTimeIncrement === ""}
          variant="contained"
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TimeIncrementDialog;

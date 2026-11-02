// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import React from "react";

interface ResetConfirmationDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

/**
 * Dialog component that asks for confirmation when resetting agent and scenario
 * when switching between views.
 */
const ResetConfirmationDialog: React.FC<ResetConfirmationDialogProps> = ({
  open,
  onClose,
  onConfirm,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="reset-confirmation-dialog-title"
      aria-describedby="reset-confirmation-dialog-description"
    >
      <DialogTitle id="reset-confirmation-dialog-title">
        Reset Agent and Scenario?
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="reset-confirmation-dialog-description">
          Switching views will reset the agent and scenario to{" "}
          <strong>default</strong>. Do you want to continue?
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          color="primary"
          variant="contained"
          autoFocus
        >
          Continue
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ResetConfirmationDialog;

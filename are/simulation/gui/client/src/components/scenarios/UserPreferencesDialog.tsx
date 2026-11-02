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
  FormControlLabel,
  Switch,
} from "@mui/material";
import { useState } from "react";
import { useAppContext } from "../../contexts/AppContextProvider";

interface UserPreferencesDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * UserPreferencesDialog component that displays a dialog for user preferences.
 *
 * @param {boolean} isOpen - Determines if the dialog is open.
 * @param {function} onClose - Function to call when the dialog is closed.
 */
const UserPreferencesDialog = ({
  isOpen,
  onClose,
}: UserPreferencesDialogProps) => {
  const { userPreferences, setUserPreferences } = useAppContext();
  const [enhanceReadability, setEnhanceReadability] = useState<boolean>(
    userPreferences.annotator.enhanceReadability,
  );

  const handleConfirm = () => {
    setUserPreferences({
      ...userPreferences,
      annotator: {
        ...userPreferences.annotator,
        enhanceReadability,
      },
    });
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>User Preferences</DialogTitle>
      <DialogContent>
        <FormControlLabel
          control={
            <Switch
              checked={enhanceReadability}
              onChange={(_, isChecked) => setEnhanceReadability(isChecked)}
            />
          }
          label="Enhance event readability"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleConfirm}>
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserPreferencesDialog;

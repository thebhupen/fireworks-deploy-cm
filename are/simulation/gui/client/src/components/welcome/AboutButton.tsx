// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import InfoIcon from "@mui/icons-material/Info";
import { useEffect, useState } from "react";
import SidebarButton from "../layout/sidebar/SidebarButton";
import { WelcomeDialog } from "./WelcomeDialog";

const TWO_DAYS_IN_MILLISECONDS = 2 * 24 * 60 * 60 * 1000;
const WELCOME_DIALOG_LAST_OPENED_AT_KEY = "welcomeDialogLastOpenedAt";

const AboutButton = ({ showLabel = false }: { showLabel?: boolean }) => {
  const [isOpen, setIsOpen] = useState(false);

  let WelcomeDialogComponent = WelcomeDialog;

  // Check if the dialog should be opened based on the last opened time.
  useEffect(() => {
    const lastOpenedTime = localStorage.getItem(
      WELCOME_DIALOG_LAST_OPENED_AT_KEY,
    );
    if (lastOpenedTime) {
      const currentTime = new Date().getTime();
      const timeDiff = currentTime - parseInt(lastOpenedTime);
      if (timeDiff >= TWO_DAYS_IN_MILLISECONDS) {
        setIsOpen(true);
      }
    } else {
      setIsOpen(true); // Default to true if no previous open time is found.
    }
  }, []);

  // Update the last opened time when the dialog is opened.
  useEffect(() => {
    if (isOpen) {
      localStorage.setItem(
        WELCOME_DIALOG_LAST_OPENED_AT_KEY,
        new Date().getTime().toString(),
      );
    }
  }, [isOpen]);

  return (
    WelcomeDialogComponent && (
      <>
        <SidebarButton
          label="About"
          startIcon={<InfoIcon fontSize="small" />}
          onClick={() => setIsOpen(true)}
          isExpanded={showLabel}
        />
        <WelcomeDialogComponent
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
        />
      </>
    )
  );
};

export default AboutButton;

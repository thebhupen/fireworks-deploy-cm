// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloseIcon from "@mui/icons-material/Close";
import {
  Alert,
  Box,
  Button,
  IconButton,
  Snackbar,
  SnackbarCloseReason,
} from "@mui/material";
import React, { createContext, useCallback, useState } from "react";

export type NotificationType = "info" | "success" | "warning" | "error";

export interface Notification {
  // The message to be displayed in the notification. This is also the key for the notification.
  message: string;
  // The type of notification, which can be "info", "success", "warning", or "error". This is optional.
  type: NotificationType;
  // The duration in milliseconds for which the notification should be displayed before automatically hiding. This is optional.
  timeout?: number;
}

export type Notify = (notification: Notification) => void;

export interface NotificationsContextType {
  snackPack: readonly Notification[];
  notify: Notify;
  clear: () => void;
}

export const NotificationsContext = createContext<NotificationsContextType>({
  snackPack: [],
  notify: () => {},
  clear: () => {},
});

interface NotificationsContextProviderProps {
  children: React.ReactNode;
  value?: Partial<NotificationsContextType>;
}

const DEFAULT_TIMEOUT = 5000;

/**
 * NotificationsContextProvider is a React functional component that provides
 * a context for managing notifications within the application. It maintains
 * a queue of notifications and handles their display using a Snackbar component.
 *
 * @param {NotificationsContextProviderProps} props - The props for the component,
 * including children and an optional initial value for the context.
 *
 * @returns {JSX.Element} The provider component that wraps its children with
 * the NotificationsContext.
 */
const NotificationsContextProvider: React.FC<
  NotificationsContextProviderProps
> = ({ children, value }) => {
  const [snackPack, setSnackPack] = useState<readonly Notification[]>(
    value?.snackPack ?? [],
  );
  const [activeNotification, setActiveNotification] =
    useState<Notification | null>(null);
  const [showClearAll, setShowClearAll] = useState(false);

  const notify = (notification: Notification) => {
    const existingNotificationIndex = snackPack.findIndex(
      (existingNotification) =>
        existingNotification.message === notification.message,
    );
    if (existingNotificationIndex !== -1) {
      setSnackPack((prev) => {
        const updatedSnackPack = [...prev];
        updatedSnackPack.splice(existingNotificationIndex, 1);
        return [notification, ...updatedSnackPack];
      });
    } else {
      setSnackPack((prev) => [notification, ...prev]);
    }
    setActiveNotification(notification);
  };

  const clear = () => {
    setActiveNotification(null);
    setSnackPack([]);
  };

  const handleClose = (
    _: React.SyntheticEvent | Event,
    reason?: SnackbarCloseReason,
  ) => {
    if (reason === "clickaway") {
      return;
    }
    setActiveNotification(null);
    const updatedSnackPack = snackPack.slice(1);
    setSnackPack(updatedSnackPack);
    if (updatedSnackPack.length) {
      setActiveNotification({ ...updatedSnackPack[0] });
    }
  };

  const handleExited = () => {
    setActiveNotification(null);
  };

  const handleMouseEnter = useCallback(() => {
    if (snackPack.length > 1) {
      setShowClearAll(true);
    }
  }, [snackPack]);

  return (
    <NotificationsContext.Provider
      value={{
        snackPack,
        notify,
        clear,
      }}
    >
      <Snackbar
        key={activeNotification ? activeNotification.message : undefined}
        open={!!activeNotification}
        autoHideDuration={DEFAULT_TIMEOUT}
        onClose={handleClose}
        TransitionProps={{ onExited: handleExited }}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowClearAll(false)}
      >
        <Box
          display={"flex"}
          flexDirection={"column"}
          alignItems={"flex-end"}
          gap={1}
          maxWidth={600}
          minWidth={300}
        >
          {showClearAll && (
            <Button color="lightgrey" onClick={() => clear()}>
              Clear All
            </Button>
          )}
          <Alert
            severity={activeNotification?.type ?? "info"}
            action={
              <IconButton
                aria-label="close"
                color="inherit"
                sx={{ p: 0.5 }}
                onClick={handleClose}
              >
                <CloseIcon />
              </IconButton>
            }
          >
            {activeNotification ? activeNotification.message : undefined}
          </Alert>
        </Box>
      </Snackbar>
      {children}
    </NotificationsContext.Provider>
  );
};

export const useNotifications = () => {
  const { notify, clear } = React.useContext(
    NotificationsContext,
  ) as NotificationsContextType;
  return { notify, clear };
};

export default NotificationsContextProvider;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import CloseIcon from "@mui/icons-material/Close";
import DownloadIcon from "@mui/icons-material/Download";
import {
  Backdrop,
  Box,
  Button,
  Collapse,
  IconButton,
  Paper,
  Toolbar,
  Typography,
  useTheme,
} from "@mui/material";
import { motion } from "framer-motion";
import React, { useEffect, useRef, useState } from "react";
import { ResizableBox } from "react-resizable";
import { useAppContext } from "../../contexts/AppContextProvider";
import { jsonToCsv, toStringCSV } from "../../utils/jsonToCsv";
import { AppExtraData, AppName, AppState } from "../../utils/types";
import ApartmentsTab from "../apartments/ApartmentsTab";
import AppsRawStateJson from "../AppsRawStateJson";
import AppsToolsInfo from "../AppsToolsInfo";
import CabTab from "../cab/CabTab";
import CalendarAppTab from "../calendar/CalendarAppTab";
import { TabProps, Tabs } from "../common/Tabs";
import ContactsTab from "../contacts/ContactsTab";
import EmailTab from "../email/EmailTab";
import { EmailClientApp } from "../email/types";
import FileSystemTab from "../filesystem/FileSystemTab";
import { FileSystemApp } from "../filesystem/types";
import CityTab from "../geography/CityTab";
import { CityApp } from "../geography/types";
import MessageTab from "../messaging/MessagesTab";
import { MessagingApp } from "../messaging/types";
import ShoppingTab from "../shopping/ShoppingTab";
import ToolInfo from "../ToolInfo";
export const APP_DRAWER_BACKDROP_Z_INDEX = 100;

const MIN_WIDTH = 800;

function getDownloadablePaths(appName: AppName, state: any) {
  switch (appName) {
    case "EmailClientApp":
    case "EmailClientV2":
    case "Emails":
    case "Mail":
      return [
        { name: "Inbox", json: state?.folders?.INBOX?.emails ?? [] },
        { name: "Sent", json: state?.folders?.SENT?.emails ?? [] },
      ];
    case "Contacts":
    case "ContactsApp":
      return [{ name: "Contacts", json: state?.contacts ?? [] }];
    case "Calendar":
    case "CalendarApp":
      return [{ name: "Events", json: state?.events ?? [] }];
    case "Shopping":
    case "ShoppingApp":
      return [{ name: "Products", json: state?.products ?? [] }];
    case "RentAFlat":
    case "ApartmentListingApp":
      return [{ name: "Apartments", json: state?.apartments ?? [] }];
  }

  return [];
}

/**
 * AppsDrawer component that provides a context for managing the state of the application drawer.
 * It allows selecting an application and displays the corresponding view in a drawer.
 *
 * @param {Object} props - The component props.
 * @param {React.ReactNode} props.children - The child components to be rendered within the AppsDrawer.
 * @returns {JSX.Element} The rendered AppsDrawer component.
 */
export default function AppsDrawer({
  children,
}: {
  children: React.ReactNode;
}) {
  const { appsState, selectedAppName, selectedAppOptions, setSelectedApp } =
    useAppContext();
  const [isResizing, setIsResizing] = useState(false);
  const theme = useTheme();
  const { extraData } = selectedAppOptions ?? {};
  const isOpen = selectedAppName != null;
  const containerRef = useRef<
    Element | (() => Element | null) | null | undefined
  >(null);

  const handleAppDrawerClose = () => {
    setSelectedApp(null);
  };

  const selectedAppState =
    selectedAppName != null
      ? appsState.find((app) => app.app_name === selectedAppName)
      : null;

  useEffect(() => {
    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
      }
    };

    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  return (
    <Box
      ref={containerRef}
      sx={{
        display: "flex",
        flexDirection: "row",
        flexGrow: 1,
        position: "relative",
        height: "100%",
      }}
    >
      <Box sx={{ flexGrow: 1 }}>{children}</Box>
      <Backdrop
        open={isOpen}
        onClick={handleAppDrawerClose}
        sx={{ zIndex: APP_DRAWER_BACKDROP_Z_INDEX }}
      />
      <Box
        sx={{
          position: "absolute",
          height: "100%",
          maxWidth: "80%",
          width: MIN_WIDTH,
          pointerEvents: isOpen ? "auto" : "none",
        }}
      >
        <Collapse
          in={isOpen}
          orientation="horizontal"
          sx={{
            position: "absolute",
            left: 0,
            height: "100%",
            zIndex: APP_DRAWER_BACKDROP_Z_INDEX + 1,
            maxWidth: "100%",
          }}
        >
          <ResizableBox
            width={MIN_WIDTH}
            minConstraints={[MIN_WIDTH, Infinity]}
            maxConstraints={[Infinity, Infinity]}
            axis="x"
            resizeHandles={["e"]}
            onResizeStart={() => setIsResizing(true)}
            onResize={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
            style={{
              display: "flex",
              maxWidth: "100%",
              minHeight: "100%",
              maxHeight: "100%",
              flexGrow: 1,
            }}
            handle={
              <motion.span
                style={{
                  position: "absolute",
                  right: 0,
                  borderRadius: "2px",
                  cursor: "ew-resize",
                  width: "4px",
                  minHeight: "100%",
                }}
                whileHover={{
                  backgroundColor: theme.palette.primary.main,
                  boxShadow: theme.shadows[3],
                }}
                whileDrag={{
                  backgroundColor: theme.palette.primary.main,
                  boxShadow: theme.shadows[3],
                }}
                animate={
                  isResizing
                    ? {
                        backgroundColor: theme.palette.primary.main,
                        boxShadow: theme.shadows[3],
                      }
                    : undefined
                }
              />
            }
          >
            <Paper
              elevation={5}
              sx={{
                minHeight: "100%",
                display: "flex",
                flexDirection: "column",
                width: "100%",
                borderTopLeftRadius: 0,
                borderBottomLeftRadius: 0,
              }}
            >
              <Toolbar variant="dense">
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  {selectedAppName}
                </Typography>
                {selectedAppName &&
                  getDownloadablePaths(selectedAppName, selectedAppState).map(
                    ({ name, json }) => {
                      if (json.length === 0) {
                        return null;
                      }

                      return (
                        <Button
                          key={`download-button-${name}`}
                          variant="contained"
                          size="small"
                          sx={{
                            marginRight: "8px",
                          }}
                          startIcon={<DownloadIcon />}
                          onClick={() => {
                            const csv = jsonToCsv(json);
                            const a = document.createElement("a");
                            a.href = window.URL.createObjectURL(
                              new Blob([toStringCSV(csv)], {
                                type: "text/plain",
                              }),
                            );
                            a.setAttribute(
                              "download",
                              `${selectedAppName}_${name}.csv`,
                            );
                            a.click();
                          }}
                        >
                          {name}
                        </Button>
                      );
                    },
                  )}
                <IconButton onClick={handleAppDrawerClose}>
                  <CloseIcon />
                </IconButton>
              </Toolbar>
              {selectedAppName != null && (
                <Box sx={{ overflow: "auto", flexGrow: 1 }}>
                  <AppView
                    appName={selectedAppName}
                    appState={selectedAppState}
                    extraData={extraData}
                    width={"100%"}
                  />
                </Box>
              )}
            </Paper>
          </ResizableBox>
        </Collapse>
      </Box>
    </Box>
  );
}

const AppView = ({
  appName,
  appState,
  extraData,
}: {
  appName: AppName;
  appState: AppState | null;
  extraData?: AppExtraData;
  width: string;
}) => {
  if (appState == null || appState.app_name == null) {
    return (
      <BasicApp
        title={appName}
        appName={appName}
        appState={{}}
        extraData={extraData}
      />
    );
  }

  switch (appName) {
    case "EmailClientApp":
    case "EmailClientV2":
    case "Emails":
    case "Mail":
      return (
        <BasicApp
          title="Emails"
          appName={appState.app_name}
          appState={appState}
          appContent={<EmailTab state={appState as EmailClientApp} />}
          extraData={extraData}
        />
      );
    case "Cabs":
    case "CabApp":
      return (
        <BasicApp
          title="Cabs"
          appName={appState.app_name}
          appState={appState}
          appContent={<CabTab state={appState} />}
          extraData={extraData}
        />
      );
    case "Contacts":
    case "ContactsApp":
      return (
        <BasicApp
          title="Contacts"
          appName={appState.app_name}
          appState={appState}
          appContent={<ContactsTab state={appState} />}
          extraData={extraData}
        />
      );
    case "Shopping":
    case "ShoppingApp":
      return (
        <BasicApp
          title="Shopping"
          appName={appState.app_name}
          appState={appState}
          appContent={<ShoppingTab state={appState} />}
          extraData={extraData}
        />
      );
    case "Doctor's Calendar":
    case "Calendar":
    case "CalendarApp":
      return (
        <BasicApp
          title="Calendar"
          appName={appState.app_name}
          appState={appState}
          appContent={<CalendarAppTab state={appState} />}
          extraData={extraData}
        />
      );
    case "City":
    case "CityApp":
      return (
        <BasicApp
          title="Cities"
          appName={appState.app_name}
          appState={appState}
          appContent={<CityTab city={appState as CityApp} />}
          extraData={extraData}
        />
      );
    case "Chats":
    case "Messages":
    case "MessagingApp":
    case "MessagingAppV2":
    case "Messenger":
    case "MessengerV2":
    case "WhatsApp":
    case "WhatsAppV2":
      return (
        <BasicApp
          title="Messages"
          appName={appState.app_name}
          appState={appState}
          appContent={<MessageTab state={appState as MessagingApp} />}
          extraData={extraData}
        />
      );
    case "Files":
    case "SandboxLocalFileSystem":
    case "VirtualFileSystem":
      return (
        <BasicApp
          title="Files"
          appName={appState.app_name}
          appState={appState}
          appContent={<FileSystemTab state={appState as FileSystemApp} />}
          extraData={extraData}
        />
      );
    case "RentAFlat":
    case "ApartmentListingApp":
      return (
        <BasicApp
          title="Apartments"
          appName={appState.app_name}
          appState={appState}
          appContent={<ApartmentsTab state={appState} />}
          extraData={extraData}
        />
      );
    case "AgentUserInterface":
      return (
        <BasicApp
          title="Agent User Interface"
          appName={appState.app_name}
          appState={appState}
          extraData={extraData}
        />
      );
    default:
      return (
        <BasicApp
          title={appName}
          appName={appState.app_name}
          appState={appState}
          extraData={extraData}
        />
      );
  }
};

interface BasicAppViewProps {
  title: string;
  appName: string;
  appState: object;
  appContent?: React.ReactNode;
  extraData?: AppExtraData;
}

/**
 * BasicApp component that renders a set of tabs based on the provided props.
 * It includes tabs for extra data, app content, and raw state.
 *
 * @param {BasicAppViewProps} props - The props for the BasicApp component.
 * @param {string} props.title - The title of the app.
 * @param {object} props.appState - The state of the app.
 * @param {JSX.Element} [props.appContent] - The content to be displayed in the app tab.
 * @param {ExtraData} [props.extraData] - Additional data to be displayed in a separate tab.
 * @returns {JSX.Element} The rendered BasicApp component with tabs.
 */
const BasicApp: React.FC<BasicAppViewProps> = ({
  title,
  appName,
  appState,
  appContent,
  extraData,
}) => {
  const tabs: TabProps[] = [
    ...(extraData
      ? [
          {
            label: extraData.name,
            content: (
              <>
                <Typography variant="h5" color="primary" gutterBottom>
                  Raw Call Parameters
                </Typography>
                <AppsRawStateJson state={extraData.data} />
                {extraData?.data?.toolMetadata && (
                  <>
                    <Typography variant="h5" color="primary" marginTop={2}>
                      Tool Definition
                    </Typography>
                    <ToolInfo
                      selectedTool={extraData.data.toolMetadata}
                      appName={appName}
                      isRunnable={false}
                      toolParams={{}}
                    />
                  </>
                )}
              </>
            ),
          },
        ]
      : []),
    ...(appContent
      ? [
          {
            label: title,
            content: appContent,
          },
        ]
      : []),
    {
      label: "Tools",
      content: <AppsToolsInfo appName={appName} />,
    },
    {
      label: "App State",
      content: <AppsRawStateJson state={appState} />,
    },
  ];
  return <Tabs tabs={tabs} resetSelectedTabOnUpdate={true} />;
};

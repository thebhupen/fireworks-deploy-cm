// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Box,
  Divider,
  Popover,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useAppContext } from "../../../contexts/AppContextProvider";
import { AppState } from "../../../utils/types";
import { ApartmentAppDetails } from "../../apartments/ApartmentAppDetails";
import { ApartmentApp } from "../../apartments/types";
import { CabAppDetails } from "../../cab/CabAppDetails";
import { CabApp } from "../../cab/types";
import { CalendarAppDetails } from "../../calendar/CalendarAppDetails";
import { CalendarApp } from "../../calendar/types";
import { ContactsAppDetails } from "../../contacts/ContactsAppDetails";
import { ContactsApp } from "../../contacts/types";
import { EmailClientAppDetails } from "../../email/EmailClientAppDetails";
import { EmailClientApp } from "../../email/types";
import { FileSystemAppDetails } from "../../filesystem/FileSystemAppDetails";
import { FileSystemApp } from "../../filesystem/types";
import { CityAppDetails } from "../../geography/CityAppDetails";
import { CityApp } from "../../geography/types";
import AppIcon from "../../icons/AppIcon";
import { MessagingAppDetails } from "../../messaging/MessagingAppDetails";
import { MessagingApp } from "../../messaging/types";
import { ShoppingAppDetails } from "../../shopping/ShoppingAppDetails";
import { ShoppingApp } from "../../shopping/types";
import SidebarButton from "./SidebarButton";

interface AppButtonProps {
  app: AppState;
  isExpanded: boolean;
  showTooltip: boolean;
}

const AppButton = ({ app, isExpanded, showTooltip }: AppButtonProps) => {
  const theme = useTheme();
  const { selectedAppName, setSelectedApp } = useAppContext();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const appDetails = useMemo(() => getAppDetails(app), [app]);
  const handleShowDetails = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!isExpanded || appDetails !== null) {
      setAnchorEl(event.currentTarget);
    }
  };

  const handleHideDetails = () => {
    setAnchorEl(null);
  };
  return (
    <div
      key={app.app_name}
      onMouseEnter={handleShowDetails}
      onMouseLeave={handleHideDetails}
    >
      <SidebarButton
        label={app.app_name}
        startIcon={
          <AppIcon
            appName={app.app_name}
            size={16}
            color={theme.palette.text.secondary}
          />
        }
        onClick={() => {
          setSelectedApp(
            app.app_name !== selectedAppName ? app.app_name : null,
          );
        }}
        isExpanded={isExpanded}
        isSelected={selectedAppName === app.app_name}
        showTooltip={showTooltip}
      />
      <Popover
        open={anchorEl != null}
        onClose={handleHideDetails}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        disableRestoreFocus
        sx={{ pointerEvents: "none", transform: "translateX(8px)" }}
      >
        <Stack>
          {!isExpanded && (
            <Typography sx={{ paddingX: 1.5, paddingY: 1 }}>
              {app.app_name}
            </Typography>
          )}
          {appDetails && (
            <>
              {!isExpanded && <Divider />}
              <Box sx={{ paddingX: 1.5, paddingY: 1 }}>{appDetails}</Box>
            </>
          )}
        </Stack>
      </Popover>
    </div>
  );
};

const getAppDetails = (app: AppState) => {
  switch (app.app_name) {
    case "EmailClientApp":
    case "EmailClientV2":
    case "Emails":
    case "Mail":
      return <EmailClientAppDetails app={app as EmailClientApp} />;
    case "Cabs":
    case "CabApp":
      return <CabAppDetails app={app as CabApp} />;
    case "Contacts":
    case "ContactsApp":
      return <ContactsAppDetails app={app as ContactsApp} />;
    case "Shopping":
    case "ShoppingApp":
      return <ShoppingAppDetails app={app as ShoppingApp} />;
    case "Doctor's Calendar":
    case "Calendar":
    case "CalendarApp":
      return <CalendarAppDetails app={app as CalendarApp} />;
    case "City":
    case "CityApp":
      return <CityAppDetails app={app as CityApp} />;
    case "Chats":
    case "Messages":
    case "MessagingApp":
    case "MessagingAppV2":
    case "Messenger":
    case "MessengerV2":
    case "WhatsApp":
    case "WhatsAppV2":
      return <MessagingAppDetails app={app as MessagingApp} />;
    case "Files":
    case "SandboxLocalFileSystem":
    case "VirtualFileSystem":
      return <FileSystemAppDetails app={app as FileSystemApp} />;
    case "RentAFlat":
    case "ApartmentListingApp":
      return <ApartmentAppDetails app={app as ApartmentApp} />;
    default:
      return null;
  }
};

export default AppButton;

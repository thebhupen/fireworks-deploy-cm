// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import AdsClickIcon from "@mui/icons-material/AdsClick";
import ApartmentIcon from "@mui/icons-material/Apartment";
import AppsIcon from "@mui/icons-material/Apps";
import AppShortcutIcon from "@mui/icons-material/AppShortcutOutlined";
import BarChartIcon from "@mui/icons-material/BarChart";
import CalendarIcon from "@mui/icons-material/CalendarMonthOutlined";
import ChatOutlinedIcon from "@mui/icons-material/ChatOutlined";
import ContactsIcon from "@mui/icons-material/Contacts";
import CitiesIcon from "@mui/icons-material/Diversity3Outlined";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import FacebookIcon from "@mui/icons-material/Facebook";
import FavoriteIcon from "@mui/icons-material/Favorite";
import FolderIcon from "@mui/icons-material/Folder";
import ImageIcon from "@mui/icons-material/Image";
import InstagramIcon from "@mui/icons-material/Instagram";
import LanguageIcon from "@mui/icons-material/Language";
import LocalTaxiIcon from "@mui/icons-material/LocalTaxi";
import MailOutlineIcon from "@mui/icons-material/MailOutline";
import ManageSearchIcon from "@mui/icons-material/ManageSearch";
import MapIcon from "@mui/icons-material/Map";
import PermPhoneMsgIcon from "@mui/icons-material/PermPhoneMsg";
import PhoneIcon from "@mui/icons-material/Phone";
import QueryBuilderIcon from "@mui/icons-material/QueryBuilder";
import QueueMusicIcon from "@mui/icons-material/QueueMusic";
import SchoolIcon from "@mui/icons-material/School";
import SearchIcon from "@mui/icons-material/Search";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import SmartphoneIcon from "@mui/icons-material/Smartphone";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SpellcheckIcon from "@mui/icons-material/Spellcheck";
import TravelExploreIcon from "@mui/icons-material/TravelExplore";
import VerticalSplitIcon from "@mui/icons-material/VerticalSplit";
import VisibilityIcon from "@mui/icons-material/Visibility";
import WhatsAppIcon from "@mui/icons-material/WhatsApp";
import { AppName } from "../../utils/types";
export default function AppIcon({
  appName,
  size,
  color,
}: {
  appName: AppName;
  size: number;
  color: string;
}) {
  const sx = { width: size, height: size, color };

  switch (appName) {
    case "SearchAgent":
    case "SearchAgentDemo":
      return <ManageSearchIcon sx={sx} />;
    case "SearchInformationTool":
      return <TravelExploreIcon sx={sx} />;
    case "VisitTool":
      return <AdsClickIcon sx={sx} />;
    case "EmailClientApp":
    case "EmailClientV2":
    case "Emails":
    case "Mail":
      return <MailOutlineIcon sx={sx} />;
    case "Cabs":
    case "CabApp":
      return <LocalTaxiIcon sx={sx} />;
    case "Contacts":
    case "ContactsApp":
      return <ContactsIcon sx={sx} />;
    case "Shopping":
    case "ShoppingApp":
      return <ShoppingCartIcon sx={sx} />;
    case "Calendar":
    case "CalendarApp":
      return <CalendarIcon sx={sx} />;
    case "City":
    case "CityApp":
      return <CitiesIcon sx={sx} />;
    case "Messages":
      return <PermPhoneMsgIcon sx={sx} />;
    case "WhatsAppV2":
    case "WhatsApp":
      return <WhatsAppIcon sx={sx} />;
    case "Chats":
      return <SmartphoneIcon sx={sx} />;
    case "Messenger":
    case "MessengerV2":
    case "MessagingApp":
    case "MessagingAppV2":
      return <ChatOutlinedIcon sx={sx} />;
    case "Files":
    case "SandboxLocalFileSystem":
    case "VirtualFileSystem":
      return <FolderIcon sx={sx} />;
    case "SocialNetwork":
      return <AppShortcutIcon sx={sx} />;
    case "Spotify":
      return <QueueMusicIcon sx={sx} />;
    case "RentAFlat":
    case "ApartmentListingApp":
      return <ApartmentIcon sx={sx} />;
    case "AgentUserInterface":
      return <SmartToyIcon sx={sx} />;
    case "Phone":
      return <PhoneIcon sx={sx} />;
    case "Instagram":
      return <InstagramIcon sx={sx} />;
    case "Facebook":
      return <FacebookIcon sx={sx} />;
    case "visualizer":
      return <VisibilityIcon sx={sx} />;
    case "Health":
      return <FavoriteIcon sx={sx} />;
    case "BrowserApp":
    case "WebNavigation":
      return <LanguageIcon sx={sx} />;
    case "GenUI":
      return <BarChartIcon sx={sx} />;
    case "TextInspectorTool":
      return <SpellcheckIcon sx={sx} />;
    case "SystemApp":
      return <QueryBuilderIcon sx={sx} />;
    case "CleverSplit":
      return <VerticalSplitIcon sx={sx} />;
    case "Doctor's Calendar":
      return <EventAvailableIcon sx={sx} />;
    case "academia-mcp":
      return <SchoolIcon sx={sx} />;
    case "geocalc-mcp":
      return <MapIcon sx={sx} />;
    case "image-edit-mcp":
      return <ImageIcon sx={sx} />;
    case "websearch-mcp":
      return <SearchIcon sx={sx} />;
    default:
      console.warn((appName as never) + " has no defined icon in ActionStart");
      return <AppsIcon sx={sx} />;
  }
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import BookIcon from "@mui/icons-material/Book";
import MenuIcon from "@mui/icons-material/Menu";
import {
  Box,
  Divider,
  IconButton,
  Paper,
  Skeleton,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import { useAppContext } from "../../../contexts/AppContextProvider";
import { capitalize } from "../../../utils/stringUtils";
import { AppViews } from "../../../utils/types";
import LeftPanelClose from "../../icons/LeftPanelClose";
import MetaLogo from "../../icons/MetaLogo";
import MoveSelectionLeft from "../../icons/MoveSelectionLeft";
import AboutButton from "../../welcome/AboutButton";
import { APP_DRAWER_BACKDROP_Z_INDEX } from "../AppsDrawer";
import AppButton from "./AppButton";
import ReportBugButton from "./ReportBugButton";
import SidebarButton from "./SidebarButton";

const HIDDEN_APPS = ["AgentUserInterface", "SystemApp"];
const SIDEBAR_EXPANDED_KEY = "sidebarExpanded";
const COLLAPSED_WIDTH = 60;
const EXPANDED_WIDTH = 240;

const loadSidebarExpanded = () => {
  const sidebarExpanded = localStorage.getItem(SIDEBAR_EXPANDED_KEY);
  if (sidebarExpanded == null) {
    return true;
  }
  return sidebarExpanded === "true";
};

const TITLE_VARIANTS = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      delay: 0.1,
    },
  },
};

interface SidebarProps<T> {
  tabs?: {
    all: Array<{ icon: React.ReactNode; id: T; label: string }>;
    selected: T;
    setSelected: (selection: T) => void;
  };
}

const Sidebar = <T extends string>({ tabs }: SidebarProps<T>) => {
  const { appsState, setAppView, isLoadingScenario, ...context } =
    useAppContext();
  const appView = context.appView;
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState<boolean>(loadSidebarExpanded());
  const apps = appsState.filter(
    (state) => !HIDDEN_APPS.includes(state.app_name),
  );
  const handleViewChange = () => {
    setAppView(
      appView === AppViews.SCENARIOS ? AppViews.PLAYGROUND : AppViews.SCENARIOS,
    );
  };

  // Update localStorage whenever isExpanded changes
  useEffect(() => {
    localStorage.setItem(SIDEBAR_EXPANDED_KEY, JSON.stringify(isExpanded));
  }, [isExpanded]);

  let settingsButton = null;
  let loginButton = null;

  return (
    <motion.div
      viewport={{ once: true }}
      initial={{ width: isExpanded ? EXPANDED_WIDTH : COLLAPSED_WIDTH }}
      animate={{
        width: isExpanded ? EXPANDED_WIDTH : COLLAPSED_WIDTH,
        transition: { duration: 0.2 },
      }}
      style={{ zIndex: APP_DRAWER_BACKDROP_Z_INDEX + 1 }}
    >
      <Paper
        elevation={1}
        sx={{
          width: "inherit",
          height: "100vh",
          borderTopLeftRadius: 0,
          borderBottomLeftRadius: 0,
        }}
      >
        <Stack
          spacing={1}
          paddingY={2.5}
          paddingX={0.5}
          height="100%"
          borderRight={`1px solid ${theme.palette.divider}`}
          sx={{ display: "flex", flexDirection: "column" }}
        >
          <motion.div
            style={{ paddingRight: isExpanded ? 4 : 0, paddingBottom: 16 }}
            animate={{
              position: "relative",
              width: "100%",
              display: "flex",
              flexDirection: "row",
              justifyContent: isExpanded ? "right" : "center",
              alignItems: "center",
            }}
          >
            <motion.div
              key="mare"
              variants={TITLE_VARIANTS}
              initial={isExpanded ? "visible" : "hidden"}
              animate={isExpanded ? "visible" : "hidden"}
              style={{ position: "absolute", left: 12 }}
              transition={{ duration: 0.1 }}
            >
              <Stack
                direction={"row"}
                justifyContent={"center"}
                alignItems={"center"}
                sx={{ marginLeft: "-8px" }}
              >
                <MetaLogo />
                <Stack>
                  <Typography color="#808080" fontWeight={700} lineHeight={1.2}>
                    Agents Research
                  </Typography>
                  <Typography color="#808080" fontWeight={700} lineHeight={1.2}>
                    Environments
                  </Typography>
                </Stack>
              </Stack>
            </motion.div>
            <motion.div key="collapsed-header" layout exit={{ opacity: 0 }}>
              <IconButton
                onClick={() => setIsExpanded(!isExpanded)}
                color="lightgrey"
              >
                {isExpanded ? <LeftPanelClose /> : <MenuIcon />}
              </IconButton>
            </motion.div>
          </motion.div>
          <Stack spacing={1}>
            <SidebarButton
              startIcon={
                appView === AppViews.SCENARIOS ? (
                  <MoveSelectionLeft />
                ) : (
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      transform: "scale(-1, 1)",
                    }}
                  >
                    <MoveSelectionLeft />
                  </Box>
                )
              }
              label={appView ? capitalize(appView) : "Select a view"}
              isExpanded={isExpanded}
              onClick={() => {
                handleViewChange();
              }}
              animateIn
            />
            {tabs && (
              <Stack>
                <Box
                  height={"32px"}
                  display={"flex"}
                  flexDirection={"column"}
                  justifyContent={"center"}
                  paddingX={1}
                >
                  {isExpanded ? (
                    <Typography
                      variant="button"
                      fontSize={"0.8rem"}
                      padding={1}
                      sx={{
                        opacity: 0.5,
                      }}
                    >
                      Interface
                    </Typography>
                  ) : (
                    <Divider />
                  )}
                </Box>
                {tabs.all.map((tab) => (
                  <SidebarButton
                    key={tab.id}
                    startIcon={tab.icon}
                    label={tab.label}
                    isExpanded={isExpanded}
                    onClick={() => tabs.setSelected(tab.id)}
                    isSelected={tabs.selected === tab.id}
                    animateIn
                  />
                ))}
              </Stack>
            )}
          </Stack>
          <Stack
            flexGrow={1}
            sx={{
              display: "flex",
              flexDirection: "column",
              minHeight: 0, // Important for flex child to shrink below content size
              overflow: "hidden", // Prevent parent from expanding
            }}
          >
            <Box
              height={"32px"}
              display={"flex"}
              flexDirection={"column"}
              justifyContent={"center"}
              paddingX={1}
              sx={{ flexShrink: 0 }} // Keep header fixed
            >
              {isExpanded ? (
                <Tooltip
                  title={
                    "Real or simulated applications for the current environment"
                  }
                  placement="right"
                >
                  <Typography
                    variant="button"
                    fontSize={"0.8rem"}
                    padding={1}
                    sx={{
                      opacity: 0.5,
                    }}
                  >
                    Applications
                  </Typography>
                </Tooltip>
              ) : (
                <Divider />
              )}
            </Box>
            <AnimatePresence>
              <Stack
                flexGrow={1}
                sx={{
                  overflowY: "auto",
                  overflowX: "hidden",
                  minHeight: 0, // Allow the container to shrink
                  scrollbarGutter: "auto",
                }}
              >
                {isLoadingScenario
                  ? Array.from({ length: 10 }).map((_, index) => (
                      <motion.div
                        key={`app-${index}`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 / (index + 1) }}
                        exit={{ opacity: 0, transition: { duration: 0.5 } }}
                        style={{
                          height: "32px",
                          width: "100%",
                          display: "flex",
                        }}
                        layout
                      >
                        <Stack
                          direction={"row"}
                          alignItems={"center"}
                          width={"100%"}
                          spacing={1}
                          sx={{ marginX: 2, marginY: 0.5 }}
                        >
                          <Skeleton
                            variant="circular"
                            width={16}
                            height={16}
                            sx={{ marginTop: 0.5 }}
                          />
                          {isExpanded && (
                            <Skeleton
                              variant="text"
                              height={24}
                              sx={{ flexGrow: 1 }}
                            />
                          )}
                        </Stack>
                      </motion.div>
                    ))
                  : apps.map((app, index) => (
                      <motion.div
                        key={`app-${index}`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.5 }}
                        layout
                      >
                        <AppButton
                          app={app}
                          isExpanded={isExpanded}
                          showTooltip={false}
                        />
                      </motion.div>
                    ))}
              </Stack>
            </AnimatePresence>
          </Stack>
          <Stack spacing={4}>
            <Stack spacing={0.5}>
              <ReportBugButton showLabel={isExpanded} />
              <SidebarButton
                startIcon={<BookIcon fontSize="small" />}
                label="Documentation"
                isExpanded={isExpanded}
                onClick={() => {
                  window.open(
                    "https://facebookresearch.github.io/meta-agents-research-environments/",
                    "_blank",
                  );
                }}
              />
              <AboutButton showLabel={isExpanded} />
              {settingsButton}
            </Stack>
            {loginButton}
          </Stack>
        </Stack>
      </Paper>
    </motion.div>
  );
};

export default Sidebar;

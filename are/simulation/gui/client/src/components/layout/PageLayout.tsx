// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import * as React from "react";

import Box from "@mui/material/Box";
import CssBaseline from "@mui/material/CssBaseline";

import AppsDrawer from "./AppsDrawer";
import Sidebar from "./sidebar/Sidebar";

export type Tab<T extends string> = {
  icon: React.ReactNode;
  id: T;
  label: string;
};

export type TabsState<T extends string> = {
  all: Array<Tab<T>>;
  selected: T;
  setSelected: (selection: T) => void;
};

export default function PageLayout<T extends string>({
  children,
  tabs,
}: {
  children?: React.ReactNode;
  tabs?: TabsState<T>;
}): React.ReactNode | null {
  return (
    <>
      <CssBaseline />
      <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <Box
          sx={{
            display: "flex",
            flexGrow: 1,
            flexDirection: "row",
            overflow: "hidden",
            height: "100%",
          }}
        >
          <Sidebar tabs={tabs} />
          <AppsDrawer>
            <Box
              sx={{
                display: "flex",
                flexGrow: 1,
                flexDirection: "row",
                overflow: "hidden",
                height: "100%",
              }}
            >
              {children}
            </Box>
          </AppsDrawer>
        </Box>
      </Box>
    </>
  );
}

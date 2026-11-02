// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { CssBaseline } from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import theme from "./theme";

import App from "./App.tsx";
import FeatureFlagsProvider from "./contexts/FeatureFlagContextProvider.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <FeatureFlagsProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </FeatureFlagsProvider>
  </StrictMode>,
);

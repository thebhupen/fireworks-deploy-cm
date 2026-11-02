// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import AppWrapper from "./App";

const rootElement = document.getElementById("root");

if (rootElement == null) {
  throw new Error("Root element not found");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <AppWrapper />
  </React.StrictMode>,
);

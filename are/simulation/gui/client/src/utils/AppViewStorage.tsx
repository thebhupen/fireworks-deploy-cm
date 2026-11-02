// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

const APP_VIEW_KEY = "app_view";

const appViewStorage = {
  setAppView: (appView: string) => {
    localStorage.setItem(APP_VIEW_KEY, appView);
  },
  getAppView: () => {
    return localStorage.getItem(APP_VIEW_KEY);
  },
  clearAppView: () => {
    localStorage.removeItem(APP_VIEW_KEY);
  },
};
export default appViewStorage;

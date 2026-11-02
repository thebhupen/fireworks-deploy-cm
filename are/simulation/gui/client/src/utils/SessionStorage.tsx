// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { v4 as uuidv4 } from "uuid";

const SESSION_NAME = "are_simulation_session_id";
const TAB_ID = "tab_id";
const UUIDV4_REGEX =
  /^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i;

export function getSessionId() {
  // Check if a session ID is provided in the URL parameters.
  const urlParams = new URLSearchParams(window.location.search);
  const urlSessionId = urlParams.get("sid");
  if (urlSessionId && UUIDV4_REGEX.test(urlSessionId)) {
    return urlSessionId;
  }

  // Check if this is a new tab without an assigned tab_id
  if (
    !sessionStorage.getItem(TAB_ID) ||
    !sessionStorage.getItem(SESSION_NAME)
  ) {
    // Assign a unique identifier to the tab
    sessionStorage.setItem(TAB_ID, uuidv4());
    // Generate a new session ID for this new tab
    const sessionId = uuidv4();
    sessionStorage.setItem(SESSION_NAME, sessionId);
    return sessionId;
  } else {
    // For an existing tab, retrieve the existing session ID
    return sessionStorage.getItem(SESSION_NAME);
  }
}

// This function is used to clear the session ID manually.
export function clearTabSession() {
  sessionStorage.removeItem(SESSION_NAME);
  sessionStorage.removeItem(TAB_ID);
}

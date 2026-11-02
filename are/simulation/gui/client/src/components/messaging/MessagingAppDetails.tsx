// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { MessagingApp } from "./types";

export const MessagingAppDetails = ({ app }: { app: MessagingApp }) => {
  const conversations = app.conversations ?? {};
  const conversationsCount = Object.keys(conversations).length;

  return (
    <div>
      <div>Conversations: {conversationsCount}</div>
    </div>
  );
};

export default MessagingAppDetails;

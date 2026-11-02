// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

const SendConversationMessageMutation = graphql`
  mutation SendConversationMessageMutation(
    $sessionId: String!
    $messagingAppName: String!
    $conversationId: String!
    $sender: String!
    $message: String!
  ) {
    sendConversationMessage(
      sessionId: $sessionId
      messagingAppName: $messagingAppName
      conversationId: $conversationId
      sender: $sender
      message: $message
    )
  }
`;

function commitSendConversationMessage(
  environment: Environment,
  sessionId: string,
  messagingAppName: string,
  conversationId: string,
  sender: string,
  message: string,
  notify: Notify,
) {
  const variables = {
    sessionId,
    messagingAppName,
    conversationId,
    sender,
    message,
  };
  commitMutation(environment, {
    mutation: SendConversationMessageMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.log("Errors:", errors);
        notify({ message: "Errors: " + JSON.stringify(errors), type: "error" });
      } else {
        console.log("Response:", response);
      }
    },
    onError: (err: GqlError) => {
      console.error(err);
      notify({
        message: err?.messageFormat ?? "Error: " + JSON.stringify(err),
        type: "error",
      });
    },
  });
}

export default commitSendConversationMessage;

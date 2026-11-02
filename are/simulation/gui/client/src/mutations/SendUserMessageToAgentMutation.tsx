// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import type { SendUserMessageToAgentMutation } from "./__generated__/SendUserMessageToAgentMutation.graphql";

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

const SendUserMessageToAgentMutation = graphql`
  mutation SendUserMessageToAgentMutation(
    $message: String!
    $attachments: [[String!]!]
    $sessionId: String!
  ) {
    sendUserMessageToAgent(
      message: $message
      attachments: $attachments
      sessionId: $sessionId
    )
  }
`;

export type Attachment = {
  file: File;
  base64: string;
};

function commitSendUserMessageToAgent(
  environment: Environment,
  message: string,
  attachments: Attachment[],
  sessionId: string,
  notify: Notify,
  onComplete?: (messageId: string) => void,
  onError?: (error?: GqlError) => void,
) {
  const variables = {
    message,
    sessionId,
    attachments: attachments.map((attachment) => [
      attachment.file.name,
      attachment.base64,
    ]),
  };
  commitMutation<SendUserMessageToAgentMutation>(environment, {
    mutation: SendUserMessageToAgentMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.log("Errors:", errors);
        notify({ message: "Errors: " + JSON.stringify(errors), type: "error" });
        // Call the onError callback if provided
        if (onError) {
          onError();
        }
      } else {
        console.log("Response:", response);
        // The response contains the message ID that was generated for this message
        const messageId = response.sendUserMessageToAgent;
        console.log("Message ID:", messageId);

        // Call the onComplete callback with the message ID if provided
        if (onComplete && messageId) {
          onComplete(messageId);
        }
      }
    },
    onError: (err: GqlError) => {
      console.error(err);
      notify({
        message: err?.messageFormat ?? "Error: " + JSON.stringify(err),
        type: "error",
      });

      // Call the onError callback if provided
      if (onError) {
        onError(err);
      }
    },
  });
}
export default commitSendUserMessageToAgent;

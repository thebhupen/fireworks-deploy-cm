// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";

export const EditHintContentMutation = graphql`
  mutation EditEventHintMutation(
    $eventId: String!
    $hintContent: String!
    $sessionId: String!
  ) {
    editHintContent(
      eventId: $eventId
      hintContent: $hintContent
      sessionId: $sessionId
    ) {
      scenarioId
    }
  }
`;

interface Variables {
  eventId: string;
  hintContent: string;
  sessionId: string;
}

function commitEditHintContent(
  environment: Environment,
  eventId: string,
  hintContent: string,
  sessionId: string,
  notify: Notify,
): Promise<void> {
  const variables: Variables = {
    eventId,
    hintContent,
    sessionId,
  };

  return new Promise((resolve, reject) => {
    commitMutation(environment, {
      mutation: EditHintContentMutation,
      variables,
      onCompleted: (response, errors) => {
        if (errors) {
          console.log("Errors:", errors);
          notify({
            message: "Errors: " + JSON.stringify(errors),
            type: "error",
          });
          reject(errors);
        } else {
          console.log("Response:", response);
          resolve();
        }
      },
      onError: (err) => {
        console.error(err);
        notify({
          message: err?.message ?? "Error: " + JSON.stringify(err),
          type: "error",
        });
        reject(err);
      },
    });
  });
}

export default commitEditHintContent;

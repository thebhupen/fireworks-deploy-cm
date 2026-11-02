// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

function commitDeleteScenarioEvent(
  environment: Environment,
  sessionId: string,
  eventId: string,
  notify: Notify,
) {
  const variables = {
    sessionId,
    eventId,
  };
  commitMutation(environment, {
    mutation: graphql`
      mutation DeleteScenarioEventMutation(
        $sessionId: String!
        $eventId: String!
      ) {
        deleteScenarioEvent(sessionId: $sessionId, eventId: $eventId)
      }
    `,
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

export default commitDeleteScenarioEvent;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

export const addScenarioEventMutation = graphql`
  mutation AddScenarioEventMutation(
    $sessionId: String!
    $app: String!
    $function: String!
    $parameters: String!
    $predecessorEventIds: [String!]!
    $eventType: EventType!
    $eventRelativeTime: Float
    $eventTime: Float
    $eventTimeComparator: EventTimeComparator
  ) {
    addScenarioEvent(
      sessionId: $sessionId
      app: $app
      function: $function
      parameters: $parameters
      predecessorEventIds: $predecessorEventIds
      eventType: $eventType
      eventRelativeTime: $eventRelativeTime
      eventTime: $eventTime
      eventTimeComparator: $eventTimeComparator
    )
  }
`;

function commitAddScenarioEvent(
  environment: Environment,
  sessionId: string,
  app: string | null,
  functionName: string,
  parameters: string,
  predecessorEventIds: Array<string>,
  eventType: string,
  eventRelativeTime: number | null,
  eventTime: number | null,
  eventTimeComparator: string | null,
  notify: Notify,
) {
  const variables = {
    sessionId,
    app,
    function: functionName,
    parameters,
    predecessorEventIds,
    eventType,
    eventRelativeTime,
    eventTime,
    eventTimeComparator,
  };
  commitMutation(environment, {
    mutation: addScenarioEventMutation,
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

export default commitAddScenarioEvent;

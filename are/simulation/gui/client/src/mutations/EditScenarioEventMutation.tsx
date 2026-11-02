// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

export const editScenarioEventMutation = graphql`
  mutation EditScenarioEventMutation(
    $sessionId: String!
    $app: String!
    $function: String!
    $parameters: String!
    $eventId: String!
    $eventType: EventType!
    $predecessorEventIds: [String!]!
    $eventRelativeTime: Float
    $eventTime: Float
    $eventTimeComparator: EventTimeComparator
  ) {
    editScenarioEvent(
      sessionId: $sessionId
      app: $app
      function: $function
      parameters: $parameters
      eventId: $eventId
      eventType: $eventType
      predecessorEventIds: $predecessorEventIds
      eventRelativeTime: $eventRelativeTime
      eventTime: $eventTime
      eventTimeComparator: $eventTimeComparator
    )
  }
`;

function commitEditScenarioEvent(
  environment: Environment,
  sessionId: string,
  app: string | null,
  functionName: string,
  parameters: string,
  eventId: string | null,
  eventType: string,
  predecessorEventIds: Array<string>,
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
    eventId,
    eventType,
    predecessorEventIds,
    eventRelativeTime,
    eventTime,
    eventTimeComparator,
  };
  commitMutation(environment, {
    mutation: editScenarioEventMutation,
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

export default commitEditScenarioEvent;

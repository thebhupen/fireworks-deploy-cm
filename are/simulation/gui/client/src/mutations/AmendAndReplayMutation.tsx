// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

function commitAmendAndReplay(
  environment: Environment,
  sessionId: string,
  logId: string,
  content: string,
  notify: Notify,
) {
  const variables = {
    sessionId,
    logId,
    content,
  };
  commitMutation(environment, {
    mutation: graphql`
      mutation AmendAndReplayMutation(
        $sessionId: String!
        $logId: String!
        $content: String!
      ) {
        amendAndReplay(
          sessionId: $sessionId
          logId: $logId
          content: $content
        ) {
          scenarioId
        }
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

export default commitAmendAndReplay;

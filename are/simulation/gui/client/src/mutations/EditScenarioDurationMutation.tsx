// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

export const EditScenarioDurationMutation = graphql`
  mutation EditScenarioDurationMutation($sessionId: String!, $duration: Float) {
    editScenarioDuration(sessionId: $sessionId, duration: $duration)
  }
`;

function commitEditScenarioDuration(
  environment: Environment,
  sessionId: string,
  duration: number | null,
  notify: Notify,
) {
  if (duration === 0) {
    // override the duration to null to indicate that the scenario is infinite
    duration = null;
  }
  const variables = {
    sessionId,
    duration,
  };
  commitMutation(environment, {
    mutation: EditScenarioDurationMutation,
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
export default commitEditScenarioDuration;

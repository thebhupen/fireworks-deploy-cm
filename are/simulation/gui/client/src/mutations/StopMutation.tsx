// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";
import type { StopMutation as StopMutationType } from "./__generated__/StopMutation.graphql";

export const StopMutation = graphql`
  mutation StopMutation($sessionId: String!) {
    stop(sessionId: $sessionId) {
      scenarioId
    }
  }
`;

function commitStop(
  environment: Environment,
  sessionId: string,
  notify: Notify,
) {
  const variables = {
    sessionId,
  };
  commitMutation<StopMutationType>(environment, {
    mutation: StopMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.log("Errors:", errors);
        notify({ message: "Errors: " + JSON.stringify(errors), type: "error" });
      } else {
        console.log("Response: ", "Stop " + response?.stop?.scenarioId);
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
export default commitStop;

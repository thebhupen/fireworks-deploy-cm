// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";
import type { PauseMutation as PauseMutationType } from "./__generated__/PauseMutation.graphql";

export const PauseMutation = graphql`
  mutation PauseMutation($sessionId: String!) {
    pause(sessionId: $sessionId) {
      scenarioId
    }
  }
`;

function commitPause(
  environment: Environment,
  sessionId: string,
  notify: Notify,
) {
  const variables = {
    sessionId,
  };
  commitMutation<PauseMutationType>(environment, {
    mutation: PauseMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.log("Errors:", errors);
        notify({ message: "Errors: " + JSON.stringify(errors), type: "error" });
      } else {
        console.log("Response: ", "Pause " + response?.pause?.scenarioId);
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
export default commitPause;

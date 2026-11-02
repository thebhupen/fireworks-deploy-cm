// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";
import type { PlayMutation as PlayMutationType } from "./__generated__/PlayMutation.graphql";

export const PlayMutation = graphql`
  mutation PlayMutation($sessionId: String!) {
    play(sessionId: $sessionId) {
      scenarioId
    }
  }
`;

function commitPlay(
  environment: Environment,
  sessionId: string,
  notify: Notify,
) {
  const variables = {
    sessionId,
  };
  commitMutation<PlayMutationType>(environment, {
    mutation: PlayMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.log("Errors:", errors);
        notify({ message: "Errors: " + JSON.stringify(errors), type: "error" });
      } else {
        console.log("Response: ", "Play " + response?.play?.scenarioId);
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

function commitPlayAsync(
  environment: Environment,
  sessionId: string,
  notify: Notify,
): Promise<any> {
  const variables = {
    sessionId,
  };

  return new Promise((resolve, reject) => {
    commitMutation<PlayMutationType>(environment, {
      mutation: PlayMutation,
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
          console.log("Response: ", "Play " + response?.play?.scenarioId);
          resolve(response);
        }
      },
      onError: (err: GqlError) => {
        console.error(err);
        notify({
          message: err?.messageFormat ?? "Error: " + JSON.stringify(err),
          type: "error",
        });
        reject(err);
      },
    });
  });
}

export { commitPlayAsync };
export default commitPlay;

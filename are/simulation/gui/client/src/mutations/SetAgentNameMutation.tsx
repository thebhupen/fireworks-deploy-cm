// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import type { PayloadError } from "relay-runtime";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";
import type { SetAgentNameMutation as SetAgentNameMutationType } from "./__generated__/SetAgentNameMutation.graphql";

export const SetAgentNameMutation = graphql`
  mutation SetAgentNameMutation($agentId: String, $sessionId: String!) {
    setAgentName(agentId: $agentId, sessionId: $sessionId)
  }
`;

function commitSetAgent(
  environment: Environment,
  agentId: string | null,
  sessionId: string,
  notify: Notify,
  onSuccess?: (data: any) => void,
  onError?: (error: GqlError[] | readonly PayloadError[]) => void,
) {
  const variables = {
    agentId,
    sessionId,
  };
  commitMutation<SetAgentNameMutationType>(environment, {
    mutation: SetAgentNameMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.log("Errors:", errors);
        notify({ message: "Errors: " + JSON.stringify(errors), type: "error" });
        if (onError) {
          onError(errors);
        }
      } else {
        console.log("Response:", response);
        if (onSuccess) {
          onSuccess(response.setAgentName);
        }
      }
    },
    onError: (err: GqlError) => {
      console.error(err);
      notify({
        message: err?.messageFormat ?? "Error: " + JSON.stringify(err),
        type: "error",
      });
      if (onError) {
        onError([err]);
      }
    },
  });
}
export default commitSetAgent;

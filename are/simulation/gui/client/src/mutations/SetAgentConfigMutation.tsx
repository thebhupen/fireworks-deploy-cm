// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import type { SetAgentConfigMutation } from "./__generated__/SetAgentConfigMutation.graphql";

import { commitMutation, Environment } from "react-relay";
import type { PayloadError } from "relay-runtime";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

const SetAgentConfigMutation = graphql`
  mutation SetAgentConfigMutation($sessionId: String!, $agentConfig: JSON) {
    setAgentConfig(sessionId: $sessionId, agentConfig: $agentConfig)
  }
`;

function commitSetAgentConfig(
  environment: Environment,
  sessionId: string,
  notify: Notify,
  agentConfig: JSON,
  onSuccess?: (response: any) => void,
  onError?: (error: GqlError[] | readonly PayloadError[]) => void,
) {
  const variables = {
    sessionId: sessionId,
    agentConfig: agentConfig,
  };

  commitMutation<SetAgentConfigMutation>(environment, {
    mutation: SetAgentConfigMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.error("Errors:", errors);
        notify({
          message: "Error updating agent config: " + JSON.stringify(errors),
          type: "error",
        });
        if (onError) {
          onError(errors);
        }
      } else {
        console.log("Agent config update successful:", response);
        notify({
          message: "Successfully updated agent config",
          type: "success",
        });
        if (onSuccess) {
          onSuccess(response.setAgentConfig);
        }
      }
    },
    onError: (err: GqlError) => {
      console.error(err);
      notify({
        message:
          err?.messageFormat ?? "Error executing tool: " + JSON.stringify(err),
        type: "error",
      });
      if (onError) {
        onError([err]);
      }
    },
  });
}

export default commitSetAgentConfig;

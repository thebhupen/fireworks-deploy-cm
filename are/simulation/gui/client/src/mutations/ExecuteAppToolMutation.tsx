// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import type { ExecuteAppToolMutation } from "./__generated__/ExecuteAppToolMutation.graphql";

import { commitMutation, Environment } from "react-relay";
import type { PayloadError } from "relay-runtime";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

const ExecuteAppToolMutation = graphql`
  mutation ExecuteAppToolMutation(
    $sessionId: String!
    $appName: String!
    $toolName: String!
    $kwargs: String!
  ) {
    executeAppTool(
      sessionId: $sessionId
      appName: $appName
      toolName: $toolName
      kwargs: $kwargs
    ) {
      appsStateJson
      returnValue
    }
  }
`;

/**
 * Executes a tool within an app
 *
 * @param environment - The Relay environment
 * @param sessionId - The ID of the session
 * @param appName - The name of the app
 * @param toolName - The name of the tool to execute
 * @param params - The parameters to pass to the tool
 * @param notify - Function to display notifications
 * @param onSuccess - Optional callback function to be called on successful execution with the response
 * @param onError - Optional callback function to be called when an error occurs
 */
function commitExecuteAppTool(
  environment: Environment,
  sessionId: string,
  appName: string,
  toolName: string,
  params: Record<string, any>,
  notify: Notify,
  onSuccess?: (response: any) => void,
  onError?: (error: GqlError[] | readonly PayloadError[]) => void,
) {
  const variables = {
    sessionId,
    appName,
    toolName,
    kwargs: JSON.stringify(params),
  };

  commitMutation<ExecuteAppToolMutation>(environment, {
    mutation: ExecuteAppToolMutation,
    variables,
    onCompleted: (response, errors) => {
      if (errors) {
        console.error("Errors:", errors);
        notify({
          message: "Error executing tool: " + JSON.stringify(errors),
          type: "error",
        });
        if (onError) {
          onError(errors);
        }
      } else {
        console.log("Tool execution successful:", response);
        notify({
          message: `Successfully executed ${toolName} on ${appName}`,
          type: "success",
        });
        if (onSuccess) {
          onSuccess(response);
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

export default commitExecuteAppTool;

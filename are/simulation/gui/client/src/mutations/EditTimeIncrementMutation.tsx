// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { commitMutation, Environment } from "react-relay";
import { graphql } from "relay-runtime";
import { Notify } from "../contexts/NotificationsContextProvider";
import { GqlError } from "../utils/errors";

export const EditTimeIncrementMutation = graphql`
  mutation EditTimeIncrementMutation(
    $sessionId: String!
    $timeIncrement: Int!
  ) {
    editTimeIncrement(
      sessionId: $sessionId
      timeIncrementInSeconds: $timeIncrement
    )
  }
`;

function commitEditTimeIncrement(
  environment: Environment,
  sessionId: string,
  timeIncrement: number,
  notify: Notify,
) {
  const variables = {
    sessionId,
    timeIncrement,
  };
  commitMutation(environment, {
    mutation: EditTimeIncrementMutation,
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
export default commitEditTimeIncrement;

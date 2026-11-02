// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  Environment,
  Network,
  RecordSource,
  Store,
  Observable,
} from "relay-runtime";
import { useWebSocket } from "../contexts/WebSocketProvider";
import { BASE_URL } from "../utils/const";

export function fetchQuery(operation: { text: string }, variables: object) {
  return fetch(`${BASE_URL}/graphql`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: operation.text,
      variables,
    }),
  }).then((response) => response.json());
}

const useRelayEnvironment = () => {
  const { wsClient } = useWebSocket();

  const subscribe = (
    operation: { text: string },
    variables: Record<string, unknown>,
  ) => {
    return Observable.create((sink) => {
      const retrySubscription = () => {
        if (!wsClient) {
          console.error("wsClient is null");
          return;
        }

        return wsClient.subscribe(
          {
            query: operation.text,
            variables,
          },
          {
            next: sink.next.bind(sink),
            error: sink.error.bind(sink),
            complete: sink.complete.bind(sink),
          },
        );
      };
      return retrySubscription();
    });
  };

  return new Environment({
    // prettier-ignore
    // @ts-ignore
    network: Network.create(fetchQuery, subscribe),
    store: new Store(new RecordSource()),
  });
};

export default useRelayEnvironment;

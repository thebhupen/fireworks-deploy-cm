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
import { vi } from "vitest";

const fetchQuery = vi.fn().mockResolvedValue({ data: {} });

const subscribe = vi.fn().mockImplementation(() => {
  return Observable.create(() => {
    // Mock subscription that doesn't emit any data but properly handles the sink
    return {
      unsubscribe: vi.fn(),
      closed: false,
    };
  });
});

const mockEnvironment = () => {
  return new Environment({
    network: Network.create(fetchQuery, subscribe),
    store: new Store(new RecordSource()),
  });
};

export default mockEnvironment;

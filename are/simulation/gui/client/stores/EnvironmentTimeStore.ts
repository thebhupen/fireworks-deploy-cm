// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
// 
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.


import { Store } from "./Store";

export const EnvironmentTimeStore = new Store<{ environmentTime: number }>({
  initialState: { environmentTime: 0 },
});

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { ARESimulationEvent } from "../../utils/types";

export interface NodeData {
  event: ARESimulationEvent;
  nodeClass: string;
}

export enum EventEditorMode {
  Create,
  Edit,
  Clone,
}

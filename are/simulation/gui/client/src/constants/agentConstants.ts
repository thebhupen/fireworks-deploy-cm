// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

export const NO_AGENT_OPTION = "ground truth, oracle events only";

// Hugging Face Dataset Configuration
export const GAIA_V2_DATASET_NAME =
  process.env.ARE_SIMULATION_GAIA_V2_DATASET_NAME ??
  "meta-agents-research-environments/gaia2";
export const GAIA_V2_DATASET_DISPLAY_NAME =
  process.env.ARE_SIMULATION_GAIA_V2_DATASET_DISPLAY_NAME ?? "Gaia2";

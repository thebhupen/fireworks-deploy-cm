// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

// Server endpoint
export const BASE_URL: string =
  process.env.ARE_SIMULATION_CLIENT_BACKEND_URL ?? "";

// GitHub repository URL
export const GITHUB_REPO_URL: string =
  "https://github.com/facebookresearch/meta-agents-research-environments";

// Hugging Face org URL
export const HF_ORG_URL: string =
  "https://huggingface.co/meta-agents-research-environments";

// Hugging Face dataset URL
export const HF_DATASET_URL: string =
  "https://huggingface.co/datasets/meta-agents-research-environments/gaia2";

export const ARXIV_URL: string = "https://arxiv.org/abs/2509.17158";

export const DOC_URL: string =
  "https://facebookresearch.github.io/meta-agents-research-environments/";

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { useMemo } from "react";
import { graphql, useLazyLoadQuery } from "react-relay";
import { useDefaultScenarioIdQuery as useDefaultScenarioIdQueryType } from "./__generated__/useDefaultScenarioIdQuery.graphql";

const GetDefaultScenarioIdQuery = graphql`
  query useDefaultScenarioIdQuery {
    getDefaultScenarioId
  }
`;

/**
 * Custom hook to get the default scenario ID.
 *
 * This hook:
 * 1. Loads the default scenario ID from the backend via getDefaultScenarioId query
 * 2. Falls back to a hardcoded default if the query returns null/undefined
 *
 * @param fallbackScenarioId - The fallback scenario ID to use if query returns null/undefined
 * @returns The default scenario ID string
 */
export function useDefaultScenarioId(fallbackScenarioId: string): string {
  // Load default scenario ID from backend
  const defaultScenarioData = useLazyLoadQuery(
    GetDefaultScenarioIdQuery,
    {},
    { fetchPolicy: "store-and-network" },
  ) as useDefaultScenarioIdQueryType;

  // Return the scenario ID with fallback
  const defaultScenarioId = useMemo(() => {
    const queryResult = defaultScenarioData?.response?.getDefaultScenarioId;

    // Use the query result if it's a non-empty string, otherwise use fallback
    if (queryResult && typeof queryResult === "string" && queryResult.trim()) {
      return queryResult;
    }

    return fallbackScenarioId;
  }, [defaultScenarioData, fallbackScenarioId]);

  return defaultScenarioId;
}

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

export interface FeatureFlagsContextType {
  isBetaUIEnabled: boolean;
  toggleBetaUI: () => void;
}

interface FeatureFlagsState {
  isBetaUIEnabled?: boolean;
  lastModified?: string;
}

export const FeatureFlagsContext = createContext<FeatureFlagsContextType>({
  isBetaUIEnabled: true, // Shows proposed UI refresh components with new design
  toggleBetaUI: () => {},
});

interface FeatureFlagsProviderProps {
  children: ReactNode;
  initialFlags?: Partial<FeatureFlagsContextType>;
}

const LOCAL_STORAGE_KEY = "featureFlags";
const BETA_UI_ENABLED_TIMESTAMP = "2025-05-12T00:00:00Z";

const loadInitialFlags = () => {
  const storedFlags = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (storedFlags) {
    const parsedFlags: FeatureFlagsState = JSON.parse(storedFlags);

    // Check if isBetaUIEnabled is false and needs to be reset
    if (parsedFlags.isBetaUIEnabled === false) {
      const lastModified = parsedFlags.lastModified
        ? new Date(parsedFlags.lastModified)
        : null;
      const resetDate = new Date(BETA_UI_ENABLED_TIMESTAMP);

      // Reset to true if lastModified is not set or before BETA_UI_ENABLED_TIMESTAMP
      if (!lastModified || lastModified < resetDate) {
        parsedFlags.isBetaUIEnabled = true;
        parsedFlags.lastModified = new Date().toISOString();
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(parsedFlags));
      }
    }

    return parsedFlags;
  }
  return {};
};

const FeatureFlagsProvider: React.FC<FeatureFlagsProviderProps> = ({
  children,
  initialFlags = loadInitialFlags(),
}) => {
  const [isBetaUIEnabled, setIsBetaUIEnabled] = useState<boolean>(
    initialFlags?.isBetaUIEnabled ?? true,
  );

  const toggleBetaUI = () => {
    setIsBetaUIEnabled((prev) => !prev);
  };

  // Update local storage when the value changes
  useEffect(() => {
    localStorage.setItem(
      LOCAL_STORAGE_KEY,
      JSON.stringify({
        isBetaUIEnabled,
        lastModified: new Date().toISOString(),
      }),
    );
  }, [isBetaUIEnabled]);

  return (
    <FeatureFlagsContext.Provider
      value={{
        isBetaUIEnabled,
        toggleBetaUI,
      }}
    >
      {children}
    </FeatureFlagsContext.Provider>
  );
};

export const useFeatureFlags = () => {
  return useContext(FeatureFlagsContext);
};

export default FeatureFlagsProvider;

// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import React, { createContext, useContext, useState } from "react";

export interface LayoutShadowContextType {
  hasOverflowContent: boolean;
  setHasOverflowContent: React.Dispatch<React.SetStateAction<boolean>>;
}

export const LayoutShadowContext = createContext<LayoutShadowContextType>({
  hasOverflowContent: false,
  setHasOverflowContent: () => {},
});

interface LayoutShadowContextProviderProps {
  children: React.ReactNode;
  value?: Partial<LayoutShadowContextType>;
}

/**
 * LayoutShadowContextProvider is a React functional component that provides
 * a context for managing layout shadow states within the application.
 * It tracks whether content has overflow and should display shadows on headers.
 *
 * @param {LayoutShadowContextProviderProps} props - The props for the component,
 * including children and an optional initial value for the context.
 *
 * @returns {JSX.Element} The provider component that wraps its children with
 * the LayoutShadowContext.
 */
const LayoutShadowContextProvider: React.FC<
  LayoutShadowContextProviderProps
> = ({ children, value }) => {
  const [hasOverflowContent, setHasOverflowContent] = useState<boolean>(
    value?.hasOverflowContent ?? false,
  );

  return (
    <LayoutShadowContext.Provider
      value={{
        hasOverflowContent,
        setHasOverflowContent,
      }}
    >
      {children}
    </LayoutShadowContext.Provider>
  );
};

export const useLayoutShadow = () => {
  const { hasOverflowContent, setHasOverflowContent } =
    useContext(LayoutShadowContext);
  return {
    hasOverflowContent,
    setHasOverflowContent,
  };
};

export default LayoutShadowContextProvider;

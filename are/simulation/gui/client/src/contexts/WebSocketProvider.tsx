// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { Client, createClient } from "graphql-ws";
import { BASE_URL } from "../utils/const";

const WebSocketContext = createContext<{
  wsClient: Client | null;
  status: "connected" | "disconnected" | "error";
  statusChangedTime: number;
}>({
  wsClient: null,
  status: "disconnected",
  statusChangedTime: Date.now(),
});

// Custom hook to use the WebSocket context
export const useWebSocket = () => {
  return useContext(WebSocketContext);
};

// Provider component
export const WebSocketProvider = ({ children }: { children: ReactNode }) => {
  const [status, setStatus] = useState<"connected" | "disconnected" | "error">(
    "disconnected",
  );
  const [statusChangedTime, setStatusChangedTime] = useState<number>(
    Date.now(),
  );
  const [wsClient, setWsClient] = useState<Client | null>(null);

  useEffect(() => {
    const client = createClient({
      url: BASE_URL.startsWith("https")
        ? `${BASE_URL.replace("https://", "wss://")}/graphql`
        : `${BASE_URL.replace("http://", "ws://")}/graphql`,
      shouldRetry: (errOrCloseEvent) => {
        // Only retry on network errors, not on protocol errors
        if (errOrCloseEvent instanceof Error) {
          return true;
        }
        // For close events, check the code
        if (errOrCloseEvent instanceof CloseEvent) {
          // Don't retry on normal closure (1000) or going away (1001)
          return errOrCloseEvent.code !== 1000 && errOrCloseEvent.code !== 1001;
        }
        return true;
      },
      retryAttempts: 5,
      retryWait: (retries) => {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s
        const delay = Math.min(1000 * Math.pow(2, retries), 30000);
        console.log(
          `Reconnection attempt ${retries + 1}, waiting ${delay}ms before retry`,
        );
        return new Promise((resolve) => setTimeout(resolve, delay));
      },
      connectionParams: {},
      keepAlive: 10000, // 10 seconds
      on: {
        connected: () => {
          if (status !== "connected") {
            setStatusChangedTime(Date.now());
          }
          setStatus("connected");
        },
        closed: () => {
          if (status !== "disconnected") {
            setStatusChangedTime(Date.now());
          }
          setStatus("disconnected");
        },
        error: () => {
          if (status !== "error") {
            setStatusChangedTime(Date.now());
          }
          setStatus("error");
        },
      },
    });

    setWsClient(client);

    // Cleanup function to close the WebSocket connection when the component unmounts
    return () => {
      client.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <WebSocketContext.Provider value={{ wsClient, status, statusChangedTime }}>
      {children}
    </WebSocketContext.Provider>
  );
};

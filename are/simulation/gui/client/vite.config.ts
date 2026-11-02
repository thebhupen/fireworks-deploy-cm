// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
// 
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

/// <reference types="vitest/config" />

import react from "@vitejs/plugin-react";
import dotenv from "dotenv";
import dotenvExpand from "dotenv-expand";
import fs from "fs";
import path from "path";
import { defineConfig } from "vite";
import relay from "vite-plugin-relay";

function findEnvFile(startDir: string): string | null {
  let currentDir = path.resolve(startDir);
  while (true) {
    const envPath = path.join(currentDir, ".env");
    if (fs.existsSync(envPath)) {
      return envPath;
    }
    const parentDir = path.dirname(currentDir);
    // On Windows, path.dirname('C:\\') returns 'C:\\', so we need to check for this case
    if (parentDir === currentDir || parentDir === path.parse(currentDir).root) {
      return null;
    }
    currentDir = parentDir;
  }
}

const envFilePath = findEnvFile(__dirname);
if (envFilePath) {
  console.log(`Loading .env file from ${envFilePath}`);
  const myEnv = dotenv.config({ path: envFilePath });
  dotenvExpand.expand(myEnv);
} else {
  console.warn("No .env file found.");
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const hasSSLCertificates = process.env.ARE_SIMULATION_SSL_CERT_PATH && process.env.ARE_SIMULATION_SSL_KEY_PATH;

  const env = {
    ARE_SIMULATION_CLIENT_BACKEND_URL: `${hasSSLCertificates ? 'https' : 'http'}://${process.env.ARE_SIMULATION_SERVER_HOSTNAME || "localhost"}:${process.env.ARE_SIMULATION_SERVER_PORT || "8080"}`,
    ARE_SIMULATION_GAIA_V2_DATASET_NAME: process.env.ARE_SIMULATION_GAIA_V2_DATASET_NAME || "meta-agents-research-environments/gaia2",
    ARE_SIMULATION_GAIA_V2_DATASET_DISPLAY_NAME: process.env.ARE_SIMULATION_GAIA_V2_DATASET_DISPLAY_NAME || "Gaia2",
  };

  // For production we do not need any of the server settings since the serving is done by Docker
  if (mode === "production") {
    return {
      base: "",
      define: {
        process: JSON.stringify({
          env,
          versions: process.versions,
        }),
      },
      build: {
        outDir: "./build",
        emptyOutDir: true,
        assetsDir: "",
        rollupOptions: {
          output: {
            manualChunks: {
              'mui-core': ['@mui/material', '@mui/icons-material', '@mui/system'],
              'mui-x-data-grid': ['@mui/x-data-grid'],
              'mui-x-other': ['@mui/x-date-pickers', '@mui/x-tree-view', '@mui/lab'],
            }
          }
        }
      },
      plugins: [react(), relay],
    };
  }
  const hostname = process.env.ARE_SIMULATION_CLIENT_HOSTNAME || "localhost";
  const port = process.env.ARE_SIMULATION_CLIENT_PORT || "8088";

  return {
    base: `${hasSSLCertificates ? 'https' : 'http'}://${hostname}:${port}/are`,
    server: {
      host: hostname,
      port: parseInt(port, 10),
      https: hasSSLCertificates
        ? {
            cert: fs.readFileSync(path.resolve(process.env.ARE_SIMULATION_SSL_CERT_PATH!)),
            key: fs.readFileSync(path.resolve(process.env.ARE_SIMULATION_SSL_KEY_PATH!)),
          }
        : undefined,
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'mui-core': ['@mui/material', '@mui/icons-material', '@mui/system'],
            'mui-x-data-grid': ['@mui/x-data-grid'],
            'mui-x-other': ['@mui/x-date-pickers', '@mui/x-tree-view', '@mui/lab'],
          }
        }
      }
    },
    define: {
      process: JSON.stringify({
        env,
        versions: process.versions,
      }),
    },
    plugins: [react(), relay],
    test: {
      environment: "jsdom",
      exclude: ["**/node_modules/**"],
      server: {
        deps: {
          inline: [
            // Avoid an error with vitest
            // TypeError: Unknown file extension ".css" for .../node_modules/@mui/x-data-grid/esm/index.css
            "@mui/x-data-grid"
          ],
        },
      },
    },
  };
});

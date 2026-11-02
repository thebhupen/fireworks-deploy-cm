// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

import { createTheme } from "@mui/material/styles";

const SURFACE_BACKGROUND = "#1E1E1E";
const BORDER_COLOR = "#575757";

declare module "@mui/material/styles" {
  interface Palette {
    darkgrey: Palette["primary"];
    lightgrey: Palette["primary"];
    white: Palette["primary"];
  }

  interface PaletteOptions {
    darkgrey: PaletteOptions["primary"];
    lightgrey?: PaletteOptions["primary"];
    white?: PaletteOptions["primary"];
  }
}

declare module "@mui/material/Button" {
  interface ButtonPropsColorOverrides {
    darkgrey: true;
    lightgrey: true;
    white: true;
  }
}

declare module "@mui/material/IconButton" {
  interface IconButtonPropsColorOverrides {
    darkgrey: true;
    lightgrey: true;
    white: true;
  }
}

declare module "@mui/material/ButtonGroup" {
  interface ButtonGroupPropsColorOverrides {
    darkgrey: true;
    lightgrey: true;
    white: true;
  }
}

const theme = createTheme({
  palette: {
    mode: "dark",
    text: {
      secondary: "#b0b3b8",
      disabled: "#757678",
    },
    primary: {
      main: "#90CAF9",
    },
    secondary: {
      main: "#00ABFF",
    },
    background: {
      default: SURFACE_BACKGROUND,
    },
    error: {
      main: "#f25449",
    },
    darkgrey: {
      main: "#383838",
    },
    lightgrey: {
      main: "#AEAFAF",
    },
    white: {
      main: "#fff",
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 550,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        // Global scrollbar styles
        "*": {
          scrollbarWidth: "thin",
          scrollbarColor: "rgba(255, 255, 255, 0.3) transparent",
          "&::-webkit-scrollbar": {
            width: "4px",
          },
          "&::-webkit-scrollbar-track": {
            background: "transparent",
          },
          "&::-webkit-scrollbar-thumb": {
            background: "rgba(255, 255, 255, 0.2)",
            borderRadius: "2px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            background: "rgba(255, 255, 255, 0.3)",
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${BORDER_COLOR}`,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiCardHeader: {
      styleOverrides: {
        root: {
          paddingBottom: 0,
        },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: {
          marginLeft: 0,
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          "&.Mui-focused": {
            color: "#2d72d2",
          },
        },
      },
    },
    MuiMenu: {
      defaultProps: {
        slotProps: {
          paper: {
            sx: { borderRadius: 2, marginTop: 1 },
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "#2d72d2",
          },
        },
      },
    },
    MuiAccordionSummary: {
      styleOverrides: {
        content: {
          margin: 0,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: "none",
        },
      },
    },
    MuiTablePagination: {
      styleOverrides: {
        root: {
          ".MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows":
            {
              marginTop: "1em",
              marginBottom: "1em",
            },
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
        },
      },
    },
    MuiTypography: {
      styleOverrides: {
        root: {
          textTransform: "none",
        },
      },
    },
  },
  shape: {
    borderRadius: 6,
  },
});

export default theme;

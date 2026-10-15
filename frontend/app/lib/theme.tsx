import React, { useEffect } from "react";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#f54e00",
      dark: "#d04200",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#807d72",
      contrastText: "#ffffff",
    },
    success: {
      main: "#1f8a65",
      contrastText: "#ffffff",
    },
    error: {
      main: "#cf2d56",
      contrastText: "#ffffff",
    },
    background: {
      default: "#f7f7f4",
      paper: "#ffffff",
    },
    text: {
      primary: "#26251e",
      secondary: "#5a5852",
    },
    divider: "#e6e5e0",
  },
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    button: {
      textTransform: "none",
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "10px 18px",
          boxShadow: "none",
          fontWeight: 500,
          textTransform: "none",
          "&:hover": {
            boxShadow: "none",
          },
          "&.MuiButton-containedPrimary": {
            backgroundColor: "#f54e00",
            color: "#ffffff",
            backgroundImage: "none",
            boxShadow: "none",
            "&:hover": {
              backgroundColor: "#d04200",
              boxShadow: "none",
            },
          },
        },
        contained: {
          boxShadow: "none",
          backgroundImage: "none",
          "&:hover": {
            boxShadow: "none",
          },
        },
      },
      variants: [
        {
          props: { variant: "contained", color: "primary" },
          style: {
            backgroundColor: "#f54e00",
            color: "#ffffff",
            backgroundImage: "none",
            boxShadow: "none",
            "&:hover": {
              backgroundColor: "#d04200",
              boxShadow: "none",
            },
          },
        },
      ],
    },
    MuiPaper: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 9999,
          fontWeight: 500,
        },
      },
    },
  },
});

export interface AppThemeState {
  mode: "light";
  toggleMode: () => void;
}

const defaultThemeState: AppThemeState = {
  mode: "light",
  toggleMode: () => {},
};

export const useAppTheme = (): AppThemeState => defaultThemeState;

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Clear any previous dark mode preference and class
    document.documentElement.classList.remove("dark");
    try {
      localStorage.removeItem("ai_resume_theme");
    } catch {
      // Ignore if localStorage is unavailable
    }
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}

export default AppThemeProvider;

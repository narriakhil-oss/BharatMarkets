"use client";

import * as React from "react";

interface ThemeContextType {
  theme: "dark";
}

const ThemeContext = React.createContext<ThemeContextType>({
  theme: "dark",
});

export function useTheme() {
  return React.useContext(ThemeContext);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  React.useEffect(() => {
    // BharatMarkets enforces premium trading terminal dark theme
    const root = document.documentElement;
    root.classList.add("dark");
    root.style.colorScheme = "dark";
  }, []);

  return (
    <ThemeContext.Provider value={{ theme: "dark" }}>
      {children}
    </ThemeContext.Provider>
  );
}

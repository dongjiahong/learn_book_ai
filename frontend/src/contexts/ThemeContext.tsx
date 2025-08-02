/**
 * Theme context for managing application theme state
 */
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { getCurrentTheme, getAntdTheme } from '@/lib/theme';

interface ThemeContextType {
  theme: ReturnType<typeof getCurrentTheme>;
  antdTheme: ReturnType<typeof getAntdTheme>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [mounted, setMounted] = useState(false);

  // Initialize theme
  useEffect(() => {
    setMounted(true);
  }, []);

  // Update CSS custom properties for theme
  useEffect(() => {
    if (mounted) {
      const theme = getCurrentTheme();
      const root = document.documentElement;
      
      // Update CSS custom properties
      Object.entries(theme.colors).forEach(([key, value]) => {
        root.style.setProperty(`--color-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value);
      });
      
      Object.entries(theme.spacing).forEach(([key, value]) => {
        root.style.setProperty(`--spacing-${key}`, value);
      });
      
      Object.entries(theme.borderRadius).forEach(([key, value]) => {
        root.style.setProperty(`--border-radius-${key}`, value);
      });

      // Set light theme
      root.setAttribute('data-theme', 'light');
    }
  }, [mounted]);

  const theme = getCurrentTheme();
  const antdTheme = getAntdTheme();

  const value: ThemeContextType = {
    theme,
    antdTheme,
  };

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
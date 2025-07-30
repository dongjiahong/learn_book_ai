/**
 * Theme configuration and utilities
 */
import { theme } from 'antd';

export type ThemeMode = 'light' | 'dark' | 'auto';

// Light theme colors
export const lightTheme = {
  colors: {
    primary: '#1890ff',
    primaryHover: '#40a9ff',
    primaryActive: '#096dd9',
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
    info: '#1890ff',
    
    // Background colors
    bgPrimary: '#ffffff',
    bgSecondary: '#fafafa',
    bgTertiary: '#f5f5f5',
    bgElevated: '#ffffff',
    
    // Text colors
    textPrimary: '#262626',
    textSecondary: '#595959',
    textTertiary: '#8c8c8c',
    textDisabled: '#bfbfbf',
    
    // Border colors
    borderPrimary: '#d9d9d9',
    borderSecondary: '#f0f0f0',
    
    // Shadow
    shadowLight: '0 2px 8px rgba(0, 0, 0, 0.06)',
    shadowMedium: '0 4px 12px rgba(0, 0, 0, 0.08)',
    shadowHeavy: '0 8px 24px rgba(0, 0, 0, 0.12)',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
  },
};

// Dark theme colors
export const darkTheme = {
  colors: {
    primary: '#1890ff',
    primaryHover: '#40a9ff',
    primaryActive: '#096dd9',
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
    info: '#1890ff',
    
    // Background colors
    bgPrimary: '#141414',
    bgSecondary: '#1f1f1f',
    bgTertiary: '#262626',
    bgElevated: '#1f1f1f',
    
    // Text colors
    textPrimary: '#ffffff',
    textSecondary: '#d9d9d9',
    textTertiary: '#8c8c8c',
    textDisabled: '#434343',
    
    // Border colors
    borderPrimary: '#434343',
    borderSecondary: '#303030',
    
    // Shadow
    shadowLight: '0 2px 8px rgba(0, 0, 0, 0.15)',
    shadowMedium: '0 4px 12px rgba(0, 0, 0, 0.25)',
    shadowHeavy: '0 8px 24px rgba(0, 0, 0, 0.35)',
  },
  spacing: lightTheme.spacing,
  borderRadius: lightTheme.borderRadius,
};

// Ant Design theme tokens for light mode
export const antdLightTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    
    // Border radius
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,
    
    // Font
    fontFamily: 'var(--font-geist-sans), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeSM: 12,
    
    // Layout
    siderBg: '#ffffff',
    headerBg: '#ffffff',
    bodyBg: '#f5f5f5',
    
    // Box shadow
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
    boxShadowSecondary: '0 4px 12px rgba(0, 0, 0, 0.08)',
  },
  components: {
    Layout: {
      siderBg: '#ffffff',
      headerBg: '#ffffff',
      bodyBg: '#f5f5f5',
      headerHeight: 64,
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#e6f4ff',
      itemHoverBg: '#f5f5f5',
      itemActiveBg: '#e6f4ff',
      itemSelectedColor: '#1890ff',
      itemColor: '#595959',
      iconSize: 16,
      itemBorderRadius: 6,
      itemMarginInline: 8,
      itemMarginBlock: 4,
    },
    Button: {
      borderRadius: 6,
      controlHeight: 32,
      controlHeightLG: 40,
      controlHeightSM: 24,
    },
    Card: {
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
    },
    Input: {
      borderRadius: 6,
      controlHeight: 32,
      controlHeightLG: 40,
      controlHeightSM: 24,
    },
    Select: {
      borderRadius: 6,
      controlHeight: 32,
      controlHeightLG: 40,
      controlHeightSM: 24,
    },
  },
};

// Ant Design theme tokens for dark mode
export const antdDarkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    ...antdLightTheme.token,
    siderBg: '#1f1f1f',
    headerBg: '#1f1f1f',
    bodyBg: '#141414',
  },
  components: {
    ...antdLightTheme.components,
    Layout: {
      siderBg: '#1f1f1f',
      headerBg: '#1f1f1f',
      bodyBg: '#141414',
      headerHeight: 64,
    },
    Menu: {
      ...antdLightTheme.components.Menu,
      itemBg: 'transparent',
      itemSelectedBg: '#111b26',
      itemHoverBg: '#262626',
      itemActiveBg: '#111b26',
      itemSelectedColor: '#1890ff',
      itemColor: '#d9d9d9',
    },
  },
};

// Responsive breakpoints
export const breakpoints = {
  xs: '480px',
  sm: '576px',
  md: '768px',
  lg: '992px',
  xl: '1200px',
  xxl: '1600px',
};

// Media queries
export const mediaQueries = {
  xs: `@media (max-width: ${breakpoints.xs})`,
  sm: `@media (max-width: ${breakpoints.sm})`,
  md: `@media (max-width: ${breakpoints.md})`,
  lg: `@media (max-width: ${breakpoints.lg})`,
  xl: `@media (max-width: ${breakpoints.xl})`,
  xxl: `@media (max-width: ${breakpoints.xxl})`,
  
  minXs: `@media (min-width: ${breakpoints.xs})`,
  minSm: `@media (min-width: ${breakpoints.sm})`,
  minMd: `@media (min-width: ${breakpoints.md})`,
  minLg: `@media (min-width: ${breakpoints.lg})`,
  minXl: `@media (min-width: ${breakpoints.xl})`,
  minXxl: `@media (min-width: ${breakpoints.xxl})`,
};

// Utility function to get current theme
export const getCurrentTheme = (mode: ThemeMode) => {
  if (mode === 'auto') {
    return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? darkTheme
      : lightTheme;
  }
  return mode === 'dark' ? darkTheme : lightTheme;
};

// Utility function to get Ant Design theme
export const getAntdTheme = (mode: ThemeMode) => {
  if (mode === 'auto') {
    return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? antdDarkTheme
      : antdLightTheme;
  }
  return mode === 'dark' ? antdDarkTheme : antdLightTheme;
};
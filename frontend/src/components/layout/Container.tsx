/**
 * Responsive container component with consistent spacing
 */
'use client';

import React from 'react';
import { Grid } from 'antd';

const { useBreakpoint } = Grid;

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  padding?: boolean;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  className = '',
  size = 'xl',
  padding = true,
}) => {
  const screens = useBreakpoint();

  const getMaxWidth = () => {
    switch (size) {
      case 'sm':
        return 'max-w-2xl';
      case 'md':
        return 'max-w-4xl';
      case 'lg':
        return 'max-w-6xl';
      case 'xl':
        return 'max-w-7xl';
      case 'full':
        return 'max-w-full';
      default:
        return 'max-w-7xl';
    }
  };

  const getPadding = () => {
    if (!padding) return '';
    
    if (screens.xs && !screens.sm) {
      return 'px-4';
    } else if (screens.sm && !screens.md) {
      return 'px-6';
    } else if (screens.md && !screens.lg) {
      return 'px-8';
    } else {
      return 'px-8';
    }
  };

  return (
    <div className={`w-full ${getMaxWidth()} mx-auto ${getPadding()} ${className}`}>
      {children}
    </div>
  );
};
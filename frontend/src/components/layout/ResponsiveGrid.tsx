/**
 * Responsive grid system component
 */
'use client';

import React from 'react';
import { Row, Col, Grid } from 'antd';
import type { RowProps, ColProps } from 'antd';

const { useBreakpoint } = Grid;

interface ResponsiveGridProps extends RowProps {
  children: React.ReactNode;
}

interface ResponsiveColProps extends ColProps {
  children: React.ReactNode;
  xs?: number | ColProps;
  sm?: number | ColProps;
  md?: number | ColProps;
  lg?: number | ColProps;
  xl?: number | ColProps;
  xxl?: number | ColProps;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  gutter = [16, 16],
  ...props
}) => {
  const screens = useBreakpoint();

  // Adjust gutter based on screen size
  const getResponsiveGutter = () => {
    if (Array.isArray(gutter)) {
      const [horizontal, vertical] = gutter;
      if (screens.xs && !screens.sm) {
        return [Math.max(8, horizontal as number), Math.max(8, vertical as number)];
      } else if (screens.sm && !screens.md) {
        return [Math.max(12, horizontal as number), Math.max(12, vertical as number)];
      }
      return gutter;
    }
    
    if (screens.xs && !screens.sm) {
      return Math.max(8, gutter as number);
    } else if (screens.sm && !screens.md) {
      return Math.max(12, gutter as number);
    }
    return gutter;
  };

  return (
    <Row gutter={getResponsiveGutter()} {...props}>
      {children}
    </Row>
  );
};

export const ResponsiveCol: React.FC<ResponsiveColProps> = ({
  children,
  xs = 24,
  sm,
  md,
  lg,
  xl,
  xxl,
  ...props
}) => {
  return (
    <Col
      xs={xs}
      sm={sm}
      md={md}
      lg={lg}
      xl={xl}
      xxl={xxl}
      {...props}
    >
      {children}
    </Col>
  );
};

// Predefined responsive column configurations
export const ResponsiveColPresets = {
  // Full width on mobile, half on tablet+
  halfOnTablet: { xs: 24, md: 12 },
  
  // Full width on mobile, third on desktop
  thirdOnDesktop: { xs: 24, lg: 8 },
  
  // Full width on mobile, quarter on large screens
  quarterOnLarge: { xs: 24, xl: 6 },
  
  // Two columns on mobile, three on tablet, four on desktop
  adaptive: { xs: 12, sm: 8, lg: 6 },
  
  // Sidebar layout: full on mobile, 1/3 on desktop
  sidebar: { xs: 24, lg: 8 },
  
  // Main content: full on mobile, 2/3 on desktop
  main: { xs: 24, lg: 16 },
};
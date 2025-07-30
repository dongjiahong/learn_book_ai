'use client';

import { ResponsiveLayout } from './ResponsiveLayout';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return <ResponsiveLayout>{children}</ResponsiveLayout>;
}
/**
 * Progress indicator component for loading states
 */
'use client';

import React from 'react';
import { Progress, Typography, Space, Grid } from 'antd';
import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { useBreakpoint } = Grid;

interface ProgressStep {
  title: string;
  description?: string;
  status: 'waiting' | 'process' | 'finish' | 'error';
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
  current: number;
  showSteps?: boolean;
  className?: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  steps,
  current,
  showSteps = true,
  className = '',
}) => {
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const getProgressPercent = () => {
    return Math.round((current / steps.length) * 100);
  };

  const getProgressStatus = () => {
    const currentStep = steps[current];
    if (!currentStep) return 'normal';
    
    switch (currentStep.status) {
      case 'error':
        return 'exception';
      case 'finish':
        return 'success';
      default:
        return 'active';
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Progress bar */}
      <Progress
        percent={getProgressPercent()}
        status={getProgressStatus()}
        strokeWidth={isMobile ? 6 : 8}
        showInfo={!isMobile}
        className="mb-4"
      />

      {/* Steps list */}
      {showSteps && (
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
                index === current
                  ? 'bg-blue-50 border border-blue-200'
                  : index < current
                  ? 'bg-green-50'
                  : 'bg-gray-50'
              }`}
            >
              {/* Step icon */}
              <div className="flex-shrink-0 mt-0.5">
                {step.status === 'finish' ? (
                  <CheckCircleOutlined className="text-green-500 text-lg" />
                ) : step.status === 'process' ? (
                  <LoadingOutlined className="text-blue-500 text-lg" spin />
                ) : step.status === 'error' ? (
                  <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                    <span className="text-white text-xs">!</span>
                  </div>
                ) : (
                  <div className={`w-5 h-5 rounded-full border-2 ${
                    index <= current
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300'
                  }`}>
                    {index < current && (
                      <CheckCircleOutlined className="text-white text-xs" />
                    )}
                  </div>
                )}
              </div>

              {/* Step content */}
              <div className="flex-1 min-w-0">
                <Text
                  strong={index === current}
                  className={`block ${
                    step.status === 'error'
                      ? 'text-red-600'
                      : index === current
                      ? 'text-blue-600'
                      : index < current
                      ? 'text-green-600'
                      : 'text-gray-600'
                  } ${isMobile ? 'text-sm' : 'text-base'}`}
                >
                  {step.title}
                </Text>
                {step.description && (
                  <Text
                    type="secondary"
                    className={`block mt-1 ${isMobile ? 'text-xs' : 'text-sm'}`}
                  >
                    {step.description}
                  </Text>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Simple progress bar component
export const SimpleProgress: React.FC<{
  percent: number;
  status?: 'normal' | 'active' | 'success' | 'exception';
  text?: string;
}> = ({ percent, status = 'active', text }) => {
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  return (
    <div className="space-y-2">
      <Progress
        percent={percent}
        status={status}
        strokeWidth={isMobile ? 6 : 8}
        showInfo={!isMobile}
      />
      {text && (
        <Text
          type="secondary"
          className={`block text-center ${isMobile ? 'text-xs' : 'text-sm'}`}
        >
          {text}
        </Text>
      )}
    </div>
  );
};
/**
 * Drag and drop file upload component
 */
'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Upload, Typography, Space, Grid } from 'antd';
import { InboxOutlined, CloudUploadOutlined } from '@ant-design/icons';
import type { UploadProps, UploadFile } from 'antd';

const { Dragger } = Upload;
const { Text, Title } = Typography;
const { useBreakpoint } = Grid;

interface DragDropUploadProps extends Omit<UploadProps, 'children'> {
  title?: string;
  description?: string;
  acceptedTypes?: string[];
  maxSize?: number; // in MB
  showFileList?: boolean;
  className?: string;
}

export const DragDropUpload: React.FC<DragDropUploadProps> = ({
  title = '拖拽文件到此处上传',
  description = '或点击选择文件',
  acceptedTypes = ['.pdf', '.epub', '.txt', '.md'],
  maxSize = 50,
  showFileList = true,
  className = '',
  ...uploadProps
}) => {
  const [dragOver, setDragOver] = useState(false);
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const beforeUpload = (file: File) => {
    // Check file type
    const isValidType = acceptedTypes.some(type => 
      file.name.toLowerCase().endsWith(type.toLowerCase())
    );
    
    if (!isValidType) {
      console.error(`文件类型不支持。支持的类型: ${acceptedTypes.join(', ')}`);
      return false;
    }

    // Check file size
    const isValidSize = file.size / 1024 / 1024 < maxSize;
    if (!isValidSize) {
      console.error(`文件大小不能超过 ${maxSize}MB`);
      return false;
    }

    return uploadProps.beforeUpload ? uploadProps.beforeUpload(file, []) : true;
  };

  return (
    <div className={className}>
      <Dragger
        {...uploadProps}
        beforeUpload={beforeUpload}
        showUploadList={showFileList}
        className={`
          transition-all duration-200 ease-in-out
          ${dragOver ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : ''}
          hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20
        `}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className={`py-8 ${isMobile ? 'px-4' : 'px-8'}`}>
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <div className={`
                rounded-full p-4 transition-colors duration-200
                ${dragOver 
                  ? 'bg-blue-100 dark:bg-blue-900/30' 
                  : 'bg-gray-100 dark:bg-gray-800'
                }
              `}>
                <InboxOutlined 
                  className={`
                    text-4xl transition-colors duration-200
                    ${dragOver 
                      ? 'text-blue-500' 
                      : 'text-gray-400 dark:text-gray-500'
                    }
                  `} 
                />
              </div>
            </div>

            <div className="space-y-2">
              <Title 
                level={isMobile ? 5 : 4} 
                className={`
                  !mb-0 transition-colors duration-200
                  ${dragOver 
                    ? 'text-blue-600 dark:text-blue-400' 
                    : 'text-gray-700 dark:text-gray-300'
                  }
                `}
              >
                {title}
              </Title>
              
              <Text 
                type="secondary" 
                className={`block ${isMobile ? 'text-sm' : 'text-base'}`}
              >
                {description}
              </Text>
            </div>

            <div className="space-y-2">
              <Text 
                type="secondary" 
                className={`block ${isMobile ? 'text-xs' : 'text-sm'}`}
              >
                支持的文件类型: {acceptedTypes.join(', ')}
              </Text>
              
              <Text 
                type="secondary" 
                className={`block ${isMobile ? 'text-xs' : 'text-sm'}`}
              >
                最大文件大小: {maxSize}MB
              </Text>
            </div>

            {isMobile && (
              <div className="pt-4">
                <Space>
                  <CloudUploadOutlined />
                  <Text className="text-sm">点击选择文件</Text>
                </Space>
              </div>
            )}
          </div>
        </div>
      </Dragger>
    </div>
  );
};
/**
 * Hook for auto-saving form data to localStorage
 */
'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useNotification } from '@/components/feedback/NotificationProvider';

interface UseAutoSaveOptions {
  key: string;
  data: any;
  delay?: number;
  enabled?: boolean;
  onSave?: (data: any) => void;
  onRestore?: (data: any) => void;
}

export const useAutoSave = ({
  key,
  data,
  delay = 2000,
  enabled = true,
  onSave,
  onRestore,
}: UseAutoSaveOptions) => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const lastSavedRef = useRef<string>('');
  const { info } = useNotification();

  // Save data to localStorage
  const saveData = useCallback((dataToSave: any) => {
    try {
      const serializedData = JSON.stringify(dataToSave);
      
      // Only save if data has changed
      if (serializedData !== lastSavedRef.current) {
        localStorage.setItem(`autosave_${key}`, serializedData);
        localStorage.setItem(`autosave_${key}_timestamp`, Date.now().toString());
        lastSavedRef.current = serializedData;
        
        if (onSave) {
          onSave(dataToSave);
        }
      }
    } catch (error) {
      console.error('Failed to auto-save data:', error);
    }
  }, [key, onSave]);

  // Restore data from localStorage
  const restoreData = useCallback(() => {
    try {
      const savedData = localStorage.getItem(`autosave_${key}`);
      const timestamp = localStorage.getItem(`autosave_${key}_timestamp`);
      
      if (savedData && timestamp) {
        const parsedData = JSON.parse(savedData);
        const saveTime = new Date(parseInt(timestamp));
        const now = new Date();
        const hoursDiff = (now.getTime() - saveTime.getTime()) / (1000 * 60 * 60);
        
        // Only restore if saved within last 24 hours
        if (hoursDiff < 24) {
          if (onRestore) {
            onRestore(parsedData);
          }
          
          info(
            '已恢复自动保存的数据',
            `保存时间: ${saveTime.toLocaleString()}`
          );
          
          return parsedData;
        } else {
          // Clean up old data
          clearSavedData();
        }
      }
    } catch (error) {
      console.error('Failed to restore auto-saved data:', error);
    }
    return null;
  }, [key, onRestore, info]);

  // Clear saved data
  const clearSavedData = useCallback(() => {
    localStorage.removeItem(`autosave_${key}`);
    localStorage.removeItem(`autosave_${key}_timestamp`);
    lastSavedRef.current = '';
  }, [key]);

  // Check if there's saved data
  const hasSavedData = useCallback(() => {
    return localStorage.getItem(`autosave_${key}`) !== null;
  }, [key]);

  // Auto-save effect
  useEffect(() => {
    if (!enabled || !data) return;

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout for auto-save
    timeoutRef.current = setTimeout(() => {
      saveData(data);
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, delay, enabled, saveData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    saveData: () => saveData(data),
    restoreData,
    clearSavedData,
    hasSavedData,
  };
};

// Hook for managing multiple auto-save instances
export const useMultiAutoSave = () => {
  const instances = useRef<Map<string, any>>(new Map());

  const createInstance = useCallback((options: UseAutoSaveOptions) => {
    const instance = useAutoSave(options);
    instances.current.set(options.key, instance);
    return instance;
  }, []);

  const clearAllSavedData = useCallback(() => {
    instances.current.forEach((instance) => {
      instance.clearSavedData();
    });
  }, []);

  const restoreAllData = useCallback(() => {
    const restoredData: Record<string, any> = {};
    instances.current.forEach((instance, key) => {
      const data = instance.restoreData();
      if (data) {
        restoredData[key] = data;
      }
    });
    return restoredData;
  }, []);

  return {
    createInstance,
    clearAllSavedData,
    restoreAllData,
  };
};
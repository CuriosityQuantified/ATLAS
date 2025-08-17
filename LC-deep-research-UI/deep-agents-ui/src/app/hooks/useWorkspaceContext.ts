import { useRef, useCallback } from 'react';

/**
 * Hook to track workspace context for async operations
 * Prevents race conditions when workspace switches during async operations
 */
export function useWorkspaceContext() {
  // Track the workspace ID when an operation starts
  const operationWorkspaceRef = useRef<string | null>(null);
  
  // Track active async operations
  const activeOperationsRef = useRef<Map<string, string>>(new Map());
  
  /**
   * Start tracking an async operation for a specific workspace
   * @param operationId Unique identifier for the operation
   * @param workspaceId The workspace ID when the operation started
   */
  const startOperation = useCallback((operationId: string, workspaceId: string) => {
    activeOperationsRef.current.set(operationId, workspaceId);
    return workspaceId;
  }, []);
  
  /**
   * Get the original workspace ID for an operation
   * @param operationId The operation identifier
   * @returns The workspace ID when the operation started, or null if not found
   */
  const getOperationWorkspace = useCallback((operationId: string): string | null => {
    return activeOperationsRef.current.get(operationId) || null;
  }, []);
  
  /**
   * End tracking for an async operation
   * @param operationId The operation identifier
   */
  const endOperation = useCallback((operationId: string) => {
    activeOperationsRef.current.delete(operationId);
  }, []);
  
  /**
   * Track the current workspace for a specific operation type
   * @param workspaceId The current workspace ID
   */
  const setCurrentWorkspace = useCallback((workspaceId: string | null) => {
    operationWorkspaceRef.current = workspaceId;
  }, []);
  
  /**
   * Get the tracked workspace for the current operation
   * @returns The tracked workspace ID
   */
  const getCurrentWorkspace = useCallback((): string | null => {
    return operationWorkspaceRef.current;
  }, []);
  
  return {
    startOperation,
    getOperationWorkspace,
    endOperation,
    setCurrentWorkspace,
    getCurrentWorkspace,
  };
}
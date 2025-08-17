import { useState, useCallback, useEffect } from "react";
import type { Workspace, TodoItem } from "../types/types";
import { v4 as uuidv4 } from "uuid";
import { safeStringify, createSerializableClone } from "../utils/utils";

const WORKSPACES_STORAGE_KEY = "deep-agents-workspaces";
const ACTIVE_WORKSPACE_STORAGE_KEY = "deep-agents-active-workspace";

// Helper function to clean up corrupted localStorage data
const cleanupCorruptedData = () => {
  try {
    localStorage.removeItem(WORKSPACES_STORAGE_KEY);
    localStorage.removeItem(ACTIVE_WORKSPACE_STORAGE_KEY);
    console.log('Cleaned up corrupted workspace data');
  } catch (error) {
    console.error('Failed to cleanup localStorage:', error);
  }
};

export function useWorkspaces() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);

  // Load workspaces from localStorage on mount
  useEffect(() => {
    try {
      const storedWorkspaces = localStorage.getItem(WORKSPACES_STORAGE_KEY);
      const storedActiveId = localStorage.getItem(ACTIVE_WORKSPACE_STORAGE_KEY);
      
      if (storedWorkspaces) {
        let parsedWorkspaces;
        try {
          parsedWorkspaces = JSON.parse(storedWorkspaces);
        } catch (parseError) {
          console.error('Failed to parse stored workspaces:', parseError);
          cleanupCorruptedData();
          // Create default workspace on parse error
          const firstWorkspace: Workspace = {
            id: uuidv4(),
            title: "Workspace 1",
            threadId: null,
            isActive: false,
            createdAt: new Date(),
            todos: [],
            files: {},
          };
          setWorkspaces([firstWorkspace]);
          setActiveWorkspaceId(firstWorkspace.id);
          return;
        }
        // Ensure workspaces are valid and properly formatted
        const workspacesWithDates = (Array.isArray(parsedWorkspaces) ? parsedWorkspaces : [])
          .filter((workspace: unknown): workspace is Record<string, unknown> => {
            // Validate workspace structure
            return Boolean(workspace && 
                   typeof workspace === 'object' && 
                   workspace !== null &&
                   'id' in workspace && 
                   'title' in workspace &&
                   (workspace.title !== undefined && workspace.title !== null));
          })
          .map((workspace: Record<string, unknown>): Workspace => ({
            id: String(workspace.id || ''),
            title: typeof workspace.title === 'string' ? workspace.title : String(workspace.title || 'Untitled'),
            threadId: typeof workspace.threadId === 'string' ? workspace.threadId : null,
            isActive: Boolean(workspace.isActive),
            createdAt: workspace.createdAt && typeof workspace.createdAt === 'string' ? new Date(workspace.createdAt) : new Date(),
            todos: Array.isArray(workspace.todos) ? workspace.todos.map((todo: Record<string, unknown>) => ({
              id: String(todo.id || ''),
              content: String(todo.content || ''),
              status: typeof todo.status === 'string' ? todo.status as 'pending' | 'in_progress' | 'completed' : 'pending',
              createdAt: todo.createdAt && typeof todo.createdAt === 'string' ? new Date(todo.createdAt) : undefined,
              updatedAt: todo.updatedAt && typeof todo.updatedAt === 'string' ? new Date(todo.updatedAt) : undefined,
            })) : [],
            files: workspace.files && typeof workspace.files === 'object' && workspace.files !== null ? workspace.files as Record<string, string> : {},
          }));
        // Ensure we have at least one valid workspace after filtering
        if (workspacesWithDates.length === 0) {
          console.warn('No valid workspaces found after filtering, creating default workspace');
          const firstWorkspace: Workspace = {
            id: uuidv4(),
            title: "Workspace 1",
            threadId: null,
            isActive: false,
            createdAt: new Date(),
            todos: [],
            files: {},
          };
          setWorkspaces([firstWorkspace]);
          setActiveWorkspaceId(firstWorkspace.id);
        } else {
          setWorkspaces(workspacesWithDates);
          
          // Set active workspace or create first one
          if (storedActiveId && workspacesWithDates.find((w: Workspace) => w.id === storedActiveId)) {
            setActiveWorkspaceId(storedActiveId);
          } else if (workspacesWithDates.length > 0) {
            setActiveWorkspaceId(workspacesWithDates[0].id);
          }
        }
      } else {
        // Create first workspace if none exist
        const firstWorkspace: Workspace = {
          id: uuidv4(),
          title: "Workspace 1",
          threadId: null,
          isActive: false,
          createdAt: new Date(),
          todos: [],
          files: {},
        };
        setWorkspaces([firstWorkspace]);
        setActiveWorkspaceId(firstWorkspace.id);
      }
    } catch (error) {
      console.error("Failed to load workspaces from localStorage:", error);
      cleanupCorruptedData();
      const firstWorkspace: Workspace = {
        id: uuidv4(),
        title: "Workspace 1",
        threadId: null,
        isActive: false,
        createdAt: new Date(),
        todos: [],
        files: {},
      };
      setWorkspaces([firstWorkspace]);
      setActiveWorkspaceId(firstWorkspace.id);
    }
  }, []);

  // Save workspaces to localStorage whenever they change
  useEffect(() => {
    if (workspaces.length > 0) {
      try {
        // Sanitize workspaces before saving to remove any Next.js async objects
        const sanitizedWorkspaces = workspaces.map(w => {
          // Use createSerializableClone to ensure no async objects are included
          const cleanWorkspace = createSerializableClone(w);
          
          // Ensure critical fields are present
          return {
            ...cleanWorkspace,
            id: w.id,
            title: String(w.title || 'Untitled'),
            threadId: w.threadId || null,
            isActive: Boolean(w.isActive),
            createdAt: w.createdAt instanceof Date ? w.createdAt.toISOString() : new Date().toISOString(),
            todos: Array.isArray(cleanWorkspace.todos) ? cleanWorkspace.todos : [],
            files: cleanWorkspace.files && typeof cleanWorkspace.files === 'object' ? cleanWorkspace.files : {}
          };
        });
        
        // Use safeStringify which now handles Next.js async objects
        const jsonString = safeStringify(sanitizedWorkspaces);
        
        if (jsonString) {
          localStorage.setItem(WORKSPACES_STORAGE_KEY, jsonString);
          console.log('Workspaces saved successfully:', sanitizedWorkspaces.map(w => ({ id: w.id, title: w.title })));
        } else {
          console.error('Failed to stringify workspaces - safeStringify returned null');
          
          // Fallback: save minimal workspace data
          const minimalWorkspaces = workspaces.map(w => ({
            id: w.id,
            title: String(w.title || 'Untitled'),
            threadId: w.threadId || null,
            isActive: Boolean(w.isActive),
            createdAt: w.createdAt instanceof Date ? w.createdAt.toISOString() : new Date().toISOString(),
            todos: [],
            files: {}
          }));
          
          const fallbackJson = safeStringify(minimalWorkspaces);
          if (fallbackJson) {
            localStorage.setItem(WORKSPACES_STORAGE_KEY, fallbackJson);
            console.warn('Saved minimal workspace data as fallback');
          }
        }
      } catch (error) {
        console.error("Failed to save workspaces to localStorage:", error);
        // Log detailed error information for debugging
        if (error instanceof Error) {
          console.error("Error details:", {
            message: error.message,
            stack: error.stack,
            workspacesLength: workspaces.length,
            workspaceIds: workspaces.map(w => w.id),
            workspaceTitles: workspaces.map(w => w.title)
          });
        }
      }
    }
  }, [workspaces]);

  // Save active workspace ID to localStorage
  useEffect(() => {
    if (activeWorkspaceId) {
      try {
        localStorage.setItem(ACTIVE_WORKSPACE_STORAGE_KEY, activeWorkspaceId);
      } catch (error) {
        console.error("Failed to save active workspace to localStorage:", error);
      }
    }
  }, [activeWorkspaceId]);

  const createWorkspace = useCallback((title?: string) => {
    const newWorkspaceId = uuidv4();
    
    // Get the current workspaces to calculate the title
    const currentWorkspaces = workspaces;
    
    // Calculate the proper title based on existing workspaces
    let workspaceNumber = currentWorkspaces.length + 1;
    let newTitle = title || `Workspace ${workspaceNumber}`;
    
    // Ensure unique title if not provided
    if (!title) {
      // Find the highest workspace number to avoid duplicates
      const existingNumbers = currentWorkspaces
        .map(w => {
          const match = w.title.match(/^Workspace (\d+)$/);
          return match ? parseInt(match[1]) : 0;
        })
        .filter(n => n > 0);
      
      if (existingNumbers.length > 0) {
        workspaceNumber = Math.max(...existingNumbers) + 1;
        newTitle = `Workspace ${workspaceNumber}`;
      }
    }
    
    const newWorkspace: Workspace = {
      id: newWorkspaceId,
      title: newTitle,
      threadId: null,
      isActive: false,
      createdAt: new Date(),
      todos: [],
      files: {},
    };
    
    setWorkspaces((prev) => [...prev, newWorkspace]);
    setActiveWorkspaceId(newWorkspaceId);
    
    console.log('Created new workspace:', { id: newWorkspaceId, title: newTitle });
    // Don't return anything - TabsManager expects () => void
  }, [workspaces]);

  const selectWorkspace = useCallback((workspaceId: string) => {
    setActiveWorkspaceId(workspaceId);
  }, []);

  const closeWorkspace = useCallback((workspaceId: string) => {
    setWorkspaces((prev) => {
      const filtered = prev.filter((w) => w.id !== workspaceId);
      
      // If we're closing the active workspace, switch to another one
      if (workspaceId === activeWorkspaceId) {
        if (filtered.length > 0) {
          setActiveWorkspaceId(filtered[0].id);
        } else {
          // If no workspaces left, create a new one
          const newWorkspace = {
            id: uuidv4(),
            title: "Workspace 1",
            threadId: null,
            isActive: false,
            createdAt: new Date(),
            todos: [],
            files: {},
          };
          setActiveWorkspaceId(newWorkspace.id);
          return [newWorkspace];
        }
      }
      
      return filtered;
    });
  }, [activeWorkspaceId]);

  const updateWorkspace = useCallback((
    workspaceId: string, 
    updates: Partial<Workspace>
  ) => {
    setWorkspaces((prev) =>
      prev.map((workspace) => {
        if (workspace.id === workspaceId) {
          // Simply merge the updates - safeStringify will handle serialization
          return { ...workspace, ...updates };
        }
        return workspace;
      })
    );
  }, []);

  const updateWorkspaceTodos = useCallback((
    workspaceId: string,
    todos: TodoItem[]
  ) => {
    // Pass todos directly - safeStringify will handle serialization
    updateWorkspace(workspaceId, { todos });
  }, [updateWorkspace]);

  const updateWorkspaceFiles = useCallback((
    workspaceId: string,
    files: Record<string, string>,
    options: { merge?: boolean } = { merge: true }
  ) => {
    if (options.merge) {
      // Merge new files with existing files instead of replacing
      setWorkspaces((prev) =>
        prev.map((workspace) => {
          if (workspace.id === workspaceId) {
            const mergedFiles = {
              ...workspace.files,  // Keep existing files
              ...files,            // Add/update new files
            };
            return { ...workspace, files: mergedFiles };
          }
          return workspace;
        })
      );
    } else {
      // Replace files entirely (legacy behavior if needed)
      updateWorkspace(workspaceId, { files });
    }
  }, [updateWorkspace]);

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId) || null;

  return {
    workspaces,
    activeWorkspaceId,
    activeWorkspace,
    createWorkspace,
    selectWorkspace,
    closeWorkspace,
    updateWorkspace,
    updateWorkspaceTodos,
    updateWorkspaceFiles,
  };
}
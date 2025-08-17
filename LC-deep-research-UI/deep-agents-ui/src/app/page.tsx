"use client";

import React, { useState, useCallback, useEffect } from "react";
import { useQueryState } from "nuqs";
import { ChatInterface } from "./components/ChatInterface/ChatInterface";
import { TasksFilesSidebar } from "./components/TasksFilesSidebar/TasksFilesSidebar";
import { TabsManager } from "./components/TabsManager/TabsManager";
import { SubAgentPanel } from "./components/SubAgentPanel/SubAgentPanel";
import { FileViewDialog } from "./components/FileViewDialog/FileViewDialog";
import { createClient } from "@/lib/client";
import { useAuthContext } from "@/providers/Auth";
import { useWorkspaces } from "./hooks/useWorkspaces";
import { useWorkspaceContext } from "./hooks/useWorkspaceContext";
import type { SubAgent, FileItem, TodoItem } from "./types/types";
import styles from "./page.module.scss";

export default function HomePage() {
  const { session } = useAuthContext();
  const [threadId, setThreadId] = useQueryState("threadId");
  const [selectedSubAgent, setSelectedSubAgent] = useState<SubAgent | null>(
    null,
  );
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [tabsCollapsed, setTabsCollapsed] = useState(false);
  const [isLoadingThreadState, setIsLoadingThreadState] = useState(false);
  
  // Track workspace context for async operations
  const { setCurrentWorkspace, getCurrentWorkspace } = useWorkspaceContext();

  const {
    workspaces,
    activeWorkspaceId,
    activeWorkspace,
    createWorkspace,
    selectWorkspace,
    closeWorkspace,
    updateWorkspaceTodos,
    updateWorkspaceFiles,
    updateWorkspace,
  } = useWorkspaces();

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const toggleTabs = useCallback(() => {
    setTabsCollapsed((prev) => !prev);
  }, []);

  // Sync threadId with active workspace
  useEffect(() => {
    if (activeWorkspace && activeWorkspace.threadId !== threadId) {
      setThreadId(activeWorkspace.threadId);
    }
  }, [activeWorkspace, threadId, setThreadId]);
  
  // Track the active workspace for operations
  useEffect(() => {
    if (activeWorkspaceId) {
      setCurrentWorkspace(activeWorkspaceId);
    }
  }, [activeWorkspaceId, setCurrentWorkspace]);

  // When workspace changes, update the threadId to match
  useEffect(() => {
    if (activeWorkspaceId && activeWorkspace) {
      setThreadId(activeWorkspace.threadId);
    }
  }, [activeWorkspaceId, activeWorkspace, setThreadId]);

  // When the threadId changes, grab the thread state from the graph server
  useEffect(() => {
    const fetchThreadState = async () => {
      if (!threadId || !session?.accessToken || !activeWorkspaceId) {
        setIsLoadingThreadState(false);
        return;
      }
      setIsLoadingThreadState(true);
      try {
        const client = createClient(session.accessToken);
        const state = await client.threads.getState(threadId);

        if (state.values && activeWorkspaceId) {
          const currentState = state.values as {
            todos?: TodoItem[];
            files?: Record<string, string>;
          };
          // Update the workspace with the fetched state
          updateWorkspaceTodos(activeWorkspaceId, currentState.todos || []);
          updateWorkspaceFiles(activeWorkspaceId, currentState.files || {});
        }
      } catch (error) {
        console.error("Failed to fetch thread state:", error);
      } finally {
        setIsLoadingThreadState(false);
      }
    };
    fetchThreadState();
  }, [threadId, session?.accessToken, activeWorkspaceId, updateWorkspaceTodos, updateWorkspaceFiles]);

  const handleNewThread = useCallback(() => {
    setThreadId(null);
    setSelectedSubAgent(null);
    if (activeWorkspaceId) {
      updateWorkspace(activeWorkspaceId, {
        threadId: null,
        todos: [],
        files: {},
      });
    }
  }, [setThreadId, activeWorkspaceId, updateWorkspace]);

  const handleWorkspaceSelect = useCallback((workspaceId: string) => {
    selectWorkspace(workspaceId);
    setSelectedSubAgent(null); // Clear sub-agent selection when switching workspaces
    // Track the new workspace for upcoming operations
    setCurrentWorkspace(workspaceId);
  }, [selectWorkspace, setCurrentWorkspace]);

  const handleTodosUpdate = useCallback((todos: TodoItem[]) => {
    if (activeWorkspaceId) {
      updateWorkspaceTodos(activeWorkspaceId, todos);
    }
  }, [activeWorkspaceId, updateWorkspaceTodos]);

  const handleFilesUpdate = useCallback((files: Record<string, string>) => {
    // Use the workspace that was active when the operation started
    // This prevents race conditions when workspace switches during file generation
    const targetWorkspaceId = getCurrentWorkspace() || activeWorkspaceId;
    
    if (targetWorkspaceId) {
      // Use merge option to prevent file loss
      updateWorkspaceFiles(targetWorkspaceId, files, { merge: true });
    }
  }, [activeWorkspaceId, updateWorkspaceFiles, getCurrentWorkspace]);

  const handleThreadIdUpdate = useCallback((value: string | ((old: string | null) => string | null) | null) => {
    const newThreadId = typeof value === 'function' ? value(threadId) : value;
    setThreadId(newThreadId);
    if (activeWorkspaceId) {
      updateWorkspace(activeWorkspaceId, { threadId: newThreadId });
    }
  }, [setThreadId, activeWorkspaceId, updateWorkspace, threadId]);

  return (
    <div className={styles.container}>
      <TabsManager
        workspaces={Array.isArray(workspaces) ? workspaces.filter(w => w && typeof w === 'object' && w.id) : []}
        activeWorkspaceId={activeWorkspaceId}
        onWorkspaceSelect={handleWorkspaceSelect}
        onWorkspaceCreate={createWorkspace}
        onWorkspaceClose={closeWorkspace}
        collapsed={tabsCollapsed}
        onToggleCollapse={toggleTabs}
      />
      <div className={styles.workspaceContainer}>
        <TasksFilesSidebar
          todos={activeWorkspace?.todos || []}
          files={activeWorkspace?.files || {}}
          onFileClick={setSelectedFile}
          collapsed={sidebarCollapsed}
          onToggleCollapse={toggleSidebar}
        />
        <div className={styles.mainContent}>
          <ChatInterface
            threadId={threadId}
            selectedSubAgent={selectedSubAgent}
            setThreadId={handleThreadIdUpdate}
            onSelectSubAgent={setSelectedSubAgent}
            onTodosUpdate={handleTodosUpdate}
            onFilesUpdate={handleFilesUpdate}
            onNewThread={handleNewThread}
            isLoadingThreadState={isLoadingThreadState}
          />
          {selectedSubAgent && (
            <SubAgentPanel
              subAgent={selectedSubAgent}
              onClose={() => setSelectedSubAgent(null)}
            />
          )}
        </div>
      </div>
      {selectedFile && (
        <FileViewDialog
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
        />
      )}
    </div>
  );
}

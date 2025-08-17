"use client";

import React, { useState, useCallback } from "react";
import { Plus, X, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Workspace } from "../../types/types";
import styles from "./TabsManager.module.scss";

interface TabsManagerProps {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  onWorkspaceSelect: (workspaceId: string) => void;
  onWorkspaceCreate: (title?: string) => void;
  onWorkspaceClose: (workspaceId: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const TabsManager = React.memo<TabsManagerProps>(
  ({
    workspaces,
    activeWorkspaceId,
    onWorkspaceSelect,
    onWorkspaceCreate,
    onWorkspaceClose,
    collapsed,
    onToggleCollapse,
  }) => {
    const [hoveredTab, setHoveredTab] = useState<string | null>(null);

    const handleTabClick = useCallback(
      (workspaceId: string) => {
        if (workspaceId !== activeWorkspaceId) {
          onWorkspaceSelect(workspaceId);
        }
      },
      [activeWorkspaceId, onWorkspaceSelect]
    );

    const handleCloseTab = useCallback(
      (e: React.MouseEvent, workspaceId: string) => {
        e.stopPropagation();
        onWorkspaceClose(workspaceId);
      },
      [onWorkspaceClose]
    );

    const truncateTitle = (title: unknown, maxLength: number = 20) => {
      // Defensive handling for any type of title value
      let safeTitle: string;
      
      if (typeof title === 'string') {
        safeTitle = title;
      } else if (typeof title === 'number') {
        safeTitle = String(title);
      } else if (title === null || title === undefined) {
        safeTitle = 'Untitled';
      } else if (typeof title === 'object') {
        // Handle case where title might be an object
        console.warn('Workspace title is an object, using fallback:', title);
        safeTitle = 'Untitled';
      } else {
        safeTitle = String(title);
      }
      
      // Ensure we always have a valid string
      if (!safeTitle || safeTitle === '[object Object]') {
        safeTitle = 'Untitled';
      }
      
      return safeTitle.length > maxLength ? `${safeTitle.substring(0, maxLength)}...` : safeTitle;
    };

    if (collapsed) {
      return (
        <div className={styles.tabsManagerCollapsed}>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className={styles.toggleButton}
            title="Expand tabs"
          >
            <ChevronRight size={20} />
          </Button>
          <div className={styles.collapsedIndicator}>
            <div className={styles.tabCountBadge}>
              {Array.isArray(workspaces) ? workspaces.length : 0}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className={styles.tabsManager}>
        <div className={styles.header}>
          <h2 className={styles.title}>Workspaces</h2>
          <div className={styles.headerActions}>
            <Button
              variant="ghost"
              size="sm"
              onClick={onWorkspaceCreate}
              className={styles.createButton}
              title="New workspace"
            >
              <Plus size={16} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleCollapse}
              className={styles.toggleButton}
              title="Collapse tabs"
            >
              <ChevronLeft size={20} />
            </Button>
          </div>
        </div>

        <ScrollArea className={styles.tabsList}>
          {!Array.isArray(workspaces) || workspaces.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No workspaces yet</p>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onWorkspaceCreate}
                className={styles.createFirstButton}
              >
                <Plus size={16} />
                Create first workspace
              </Button>
            </div>
          ) : (
            workspaces
              .filter(workspace => {
                // Comprehensive workspace validation
                if (!workspace || typeof workspace !== 'object') {
                  console.warn('Invalid workspace found:', workspace);
                  return false;
                }
                if (!workspace.id) {
                  console.warn('Workspace missing id:', workspace);
                  return false;
                }
                if (workspace.title === undefined || workspace.title === null) {
                  console.warn('Workspace missing title:', workspace);
                  return false;
                }
                return true;
              })
              .map((workspace) => {
                // Additional validation in map function to prevent React child errors
                const safeWorkspace = {
                  ...workspace,
                  title: typeof workspace.title === 'string' ? workspace.title : String(workspace.title || 'Untitled'),
                  todos: Array.isArray(workspace.todos) ? workspace.todos : [],
                  files: workspace.files && typeof workspace.files === 'object' ? workspace.files : {}
                };
                
                return (
              <div
                key={safeWorkspace.id}
                className={`${styles.tab} ${
                  safeWorkspace.id === activeWorkspaceId ? styles.active : ""
                }`}
                onClick={() => handleTabClick(safeWorkspace.id)}
                onMouseEnter={() => setHoveredTab(safeWorkspace.id)}
                onMouseLeave={() => setHoveredTab(null)}
              >
                <div className={styles.tabContent}>
                  <div className={styles.tabTitle}>
                    {truncateTitle(safeWorkspace.title)}
                  </div>
                  <div className={styles.tabMeta}>
                    {safeWorkspace.todos.length > 0 && (
                      <span className={styles.taskCount}>
                        {safeWorkspace.todos.length} tasks
                      </span>
                    )}
                    {Object.keys(safeWorkspace.files).length > 0 && (
                      <span className={styles.fileCount}>
                        {Object.keys(safeWorkspace.files).length} files
                      </span>
                    )}
                  </div>
                </div>
                {Array.isArray(workspaces) && workspaces.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => handleCloseTab(e, safeWorkspace.id)}
                    className={`${styles.closeButton} ${
                      hoveredTab === safeWorkspace.id || safeWorkspace.id === activeWorkspaceId
                        ? styles.visible
                        : ""
                    }`}
                    title="Close workspace"
                  >
                    <X size={14} />
                  </Button>
                )}
              </div>
                );
              })
          )}
        </ScrollArea>
      </div>
    );
  }
);

TabsManager.displayName = "TabsManager";
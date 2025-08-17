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
  onWorkspaceCreate: () => void;
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

    const truncateTitle = (title: string, maxLength: number = 20) => {
      const safeTitle = typeof title === 'string' ? title : String(title || 'Untitled');
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
          {workspaces.length === 0 ? (
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
            workspaces.filter(workspace => workspace && workspace.id && workspace.title).map((workspace) => (
              <div
                key={workspace.id}
                className={`${styles.tab} ${
                  workspace.id === activeWorkspaceId ? styles.active : ""
                }`}
                onClick={() => handleTabClick(workspace.id)}
                onMouseEnter={() => setHoveredTab(workspace.id)}
                onMouseLeave={() => setHoveredTab(null)}
              >
                <div className={styles.tabContent}>
                  <div className={styles.tabTitle}>
                    {truncateTitle(workspace.title)}
                  </div>
                  <div className={styles.tabMeta}>
                    {Array.isArray(workspace.todos) && workspace.todos.length > 0 && (
                      <span className={styles.taskCount}>
                        {workspace.todos.length} tasks
                      </span>
                    )}
                    {workspace.files && typeof workspace.files === 'object' && Object.keys(workspace.files).length > 0 && (
                      <span className={styles.fileCount}>
                        {Object.keys(workspace.files).length} files
                      </span>
                    )}
                  </div>
                </div>
                {workspaces.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => handleCloseTab(e, workspace.id)}
                    className={`${styles.closeButton} ${
                      hoveredTab === workspace.id || workspace.id === activeWorkspaceId
                        ? styles.visible
                        : ""
                    }`}
                    title="Close workspace"
                  >
                    <X size={14} />
                  </Button>
                )}
              </div>
            ))
          )}
        </ScrollArea>
      </div>
    );
  }
);

TabsManager.displayName = "TabsManager";
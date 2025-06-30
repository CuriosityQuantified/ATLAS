# Tasks Tab Redesign Specification

## Overview

Restructure the current agent monitoring interface to become the **Tasks Tab** with project-specific views and comprehensive agent dialogue tracking. Each project will have its own dedicated task monitoring page with real-time agent communication windows.

## Current State vs. Target State

### Current Implementation
- Single static agent monitoring interface
- Basic agent status cards with progress bars
- Simple questions panel on the right
- Global chat bar at bottom

### Target Implementation
- **Project-scoped task monitoring** with dropdown selector
- **Agent dialogue windows** showing full input/output conversations
- **Multi-modal content display** for all agent communications
- **Real-time AG-UI updates** for live dialogue streaming
- **Expandable/collapsible** agent windows for detailed inspection

## Interface Architecture

### Header Section
```
[ATLAS Logo] [Dashboard] [Tasks*] [Agents] [Memory] [Analytics] [Settings]
                                    ↓
            Project: [Market Analysis 2024 ▼] [New Project] [Settings]
```

### Main Layout (Tasks Tab)
```
┌─────────────────────────────────────────────────────────────────────┐
│ Project Selector & Controls                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ Global Supervisor│  │                 │  │                 │     │
│  │ Status: Active   │  │                 │  │                 │     │
│  │ Progress: 93%    │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│  ┌─────────────────┐                                               │
│  │ 💬 Dialogue     │  ← Collapsible dialogue window               │
│  │ [Input History] │                                               │
│  │ [Output Stream] │                                               │
│  │ [Media Content] │                                               │
│  └─────────────────┘                                               │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │🕵️‍♂️Research Super│  │📊Analysis Super │  │✍️Writing Super │     │
│  │ Status: Complete │  │ Status: Active  │  │ Status: Waiting │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ 💬 Dialogue     │  │ 💬 Dialogue     │  │ 💬 Dialogue     │     │
│  │ [Completed]     │  │ [Live Updates]  │  │ [Pending]       │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Worker Agents (5 agents with individual dialogue windows)   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Project Selector Dropdown
**Location**: Top of Tasks tab, below main navigation
**Features**:
- Dropdown list of all active and recent projects
- Project status indicators (Active, Completed, Paused, Failed)
- Quick project creation button
- Project settings/configuration access

**State Management**:
```typescript
interface ProjectSelector {
  selectedProject: Project | null
  availableProjects: Project[]
  onProjectChange: (projectId: string) => void
  onCreateProject: () => void
}
```

### 2. Agent Dialogue Windows
**Location**: Below each agent status card
**Features**:
- **Collapsible/Expandable**: Toggle visibility per agent
- **Input/Output Streams**: Separate sections for agent inputs and outputs
- **Multi-modal Content**: Text, images, audio, files, charts, JSON data
- **Real-time Updates**: Live streaming via AG-UI protocol
- **History Persistence**: Full conversation scrollback
- **Search & Filter**: Find specific messages or content types

**Component Structure**:
```typescript
interface AgentDialogue {
  agentId: string
  projectId: string
  isExpanded: boolean
  messages: DialogueMessage[]
  isLive: boolean
  onToggleExpand: () => void
  onSendMessage: (content: string) => void
}

interface DialogueMessage {
  id: string
  timestamp: Date
  direction: 'input' | 'output'
  contentType: 'text' | 'image' | 'audio' | 'file' | 'json' | 'chart'
  content: any
  metadata?: {
    model?: string
    tokens?: number
    cost?: number
    duration?: number
  }
}
```

### 3. Multi-modal Content Display
**Supported Content Types**:
- **Text**: Markdown rendering with syntax highlighting
- **Images**: Inline display with zoom capabilities
- **Audio**: Embedded player with waveform visualization
- **Files**: Download links with previews for supported types
- **Charts**: Interactive data visualizations
- **JSON**: Collapsible tree view with syntax highlighting
- **Code**: Syntax-highlighted code blocks
- **Tables**: Sortable, filterable data grids

### 4. AG-UI Real-time Integration
**WebSocket Connection**:
```typescript
interface AGUIConnection {
  projectId: string
  onDialogueUpdate: (agentId: string, message: DialogueMessage) => void
  onAgentStatusChange: (agentId: string, status: AgentStatus) => void
  onProjectUpdate: (project: Project) => void
}
```

**Event Types**:
- `dialogue.message.new` - New message from agent
- `dialogue.message.update` - Message content updated
- `agent.status.change` - Agent status changed
- `project.progress.update` - Overall project progress
- `agent.question.new` - Agent has a question for user

## Implementation Tasks Breakdown

### Phase 1: Core Restructuring
1. **Convert current interface to Tasks tab page**
   - Move existing Dashboard.tsx to TasksView.tsx
   - Update navigation to highlight Tasks tab
   - Add project context to page state

2. **Implement project selector dropdown**
   - Create ProjectSelector component
   - Add project state management
   - Connect to backend API for project list
   - Handle project switching

3. **Add basic dialogue windows**
   - Create AgentDialogue component
   - Implement expand/collapse functionality
   - Add basic message display (text only)
   - Position windows below agent cards

### Phase 2: Multi-modal Support
4. **Implement content type rendering**
   - Create ContentRenderer component
   - Add support for images, audio, files
   - Implement JSON and code syntax highlighting
   - Add chart/visualization support

5. **Enhanced dialogue features**
   - Add message search and filtering
   - Implement conversation persistence
   - Add message metadata display
   - Create conversation export functionality

### Phase 3: Real-time Integration
6. **AG-UI WebSocket client**
   - Implement WebSocket connection management
   - Create event handling system
   - Add automatic reconnection logic
   - Handle connection state indicators

7. **Live dialogue streaming**
   - Connect dialogue windows to AG-UI events
   - Implement real-time message updates
   - Add typing indicators and live status
   - Handle multi-user collaboration

### Phase 4: Advanced Features
8. **Performance optimization**
   - Implement virtual scrolling for long conversations
   - Add message pagination and lazy loading
   - Optimize real-time update performance
   - Add conversation caching

9. **User experience enhancements**
   - Add keyboard shortcuts for navigation
   - Implement drag-and-drop for window arrangement
   - Add conversation bookmarking
   - Create custom notification settings

## Technical Implementation Details

### State Management
```typescript
// Global state for Tasks tab
interface TasksState {
  selectedProject: Project | null
  projects: Project[]
  agents: Agent[]
  dialogues: Record<string, DialogueMessage[]>
  expandedAgents: Set<string>
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
}
```

### API Endpoints Required
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}/agents` - Get agents for project
- `GET /api/projects/{id}/dialogues` - Get dialogue history
- `POST /api/projects/{id}/messages` - Send message to agent
- `WebSocket /api/ws/projects/{id}` - Real-time updates

### Component File Structure
```
src/components/tasks/
├── TasksView.tsx           # Main tasks tab page
├── ProjectSelector.tsx     # Project dropdown
├── AgentGrid.tsx          # Agent layout manager
├── AgentDialogue.tsx      # Individual dialogue window
├── ContentRenderer.tsx    # Multi-modal content display
├── DialogueHistory.tsx    # Message list with virtualization
├── MessageInput.tsx       # User input for agent communication
└── AGUIClient.tsx         # WebSocket client component
```

## Success Criteria

### Functional Requirements
- ✅ User can switch between projects via dropdown
- ✅ Each agent displays expandable dialogue window
- ✅ Multi-modal content renders correctly in dialogues
- ✅ Real-time updates stream to appropriate dialogue windows
- ✅ Conversation history persists across sessions
- ✅ Search and filtering works across all dialogues

### Performance Requirements
- Page loads project data within 2 seconds
- Real-time updates appear within 100ms of server event
- Smooth scrolling in dialogue windows with 1000+ messages
- WebSocket reconnection within 5 seconds of connection loss

### User Experience Requirements
- Intuitive navigation between projects and agent dialogues
- Clear visual indicators for agent status and activity
- Responsive design works on desktop and tablet
- Keyboard shortcuts for common actions

This redesign transforms the current static agent monitoring into a dynamic, project-focused workspace where users can deeply inspect and interact with agent conversations across all modalities.
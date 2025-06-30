# ATLAS Dashboard Specification

## Overview

The ATLAS Dashboard serves as the central command center and homepage for users to manage projects, monitor system performance, and access all generated content. This is distinct from the Task Execution interface which shows live agent activity during active analysis tasks.

## Dashboard Purpose

### Primary Functions
1. **Project Management**: Overview of all analysis projects (active, completed, archived)
2. **Performance Monitoring**: System metrics, costs, and quality indicators
3. **Content Access**: Quick links to reports, documents, and generated artifacts
4. **Activity Tracking**: Recent system activity and task history
5. **Workflow Optimization**: AI-suggested next steps and project recommendations
6. **Resource Management**: Budget tracking, usage analytics, and capacity planning

## Interface Layout

### Header Section
- **Global Navigation**: Dashboard, Projects, Analytics, Settings, Help
- **User Profile**: Avatar, name, role, account settings
- **Notifications**: System alerts, agent questions, task completions
- **Search Bar**: Global search across projects, files, and conversations
- **Quick Actions**: New Analysis, Import Data, Export Reports

### Main Dashboard Grid (3-Column Layout)

#### Left Column: Project Overview
**Active Projects Panel**
- Card-based display of currently running analyses
- Status indicators (Research, Analysis, Writing, Review phases)
- Progress bars and estimated completion times
- Quick access to Task Execution view for each project

**Recent Projects Panel**
- Last 5-10 completed projects
- Completion dates, quality scores, and key metrics
- One-click access to generated reports and artifacts

**Project Statistics**
- Total projects: Active (X), Completed (Y), Success rate (Z%)
- Average project duration and cost per project
- Quality score trends over time

#### Center Column: Activity & Insights
**Recent Activity Timeline**
- Agent interactions and task completions
- File generations and updates
- User actions and system events
- Filterable by date range and activity type

**Key Insights Panel**
- AI-generated summary of recent patterns
- Performance trends and optimization opportunities
- Cost analysis and budget recommendations
- Quality improvement suggestions

**Quick Metrics Cards**
- Total analyses completed this month
- Average quality score (4.2/5.0)
- Total cost this month vs. budget
- Most productive agent teams

#### Right Column: Tools & Management
**File Management Browser**
- Recent documents and reports
- Organized by project and type (PDFs, Word docs, presentations)
- Search and filter capabilities
- Direct download and sharing links

**Suggestions Engine**
- AI-recommended next analysis topics
- Follow-up questions based on completed projects
- Template suggestions for common analysis types
- Integration opportunities with existing projects

**System Status Panel**
- Agent availability and performance
- MLflow monitoring dashboard link
- Database health and storage usage
- API rate limits and quotas

### Footer Section
- **System Information**: Version, uptime, last update
- **Support Links**: Documentation, tutorials, contact support  
- **Legal**: Privacy policy, terms of service
- **External Integrations**: Connected services status

## Key Metrics Displayed

### Project Metrics
- **Project Count**: Total active, completed, and archived projects
- **Success Rate**: Percentage of projects completed successfully
- **Average Duration**: Typical time from start to completion
- **Quality Scores**: Average rating from Rating Team agents
- **Cost per Project**: Average spend including API costs and compute

### Performance Metrics
- **Agent Utilization**: Which agents are most/least active
- **Response Times**: Average time for each analysis phase
- **Error Rates**: Failed tasks and recovery success rates
- **Resource Usage**: CPU, memory, storage consumption
- **API Usage**: Token consumption across different LLM providers

### Financial Metrics
- **Monthly Spend**: Current month cost vs. budget
- **Cost Breakdown**: By LLM provider, agent type, and project
- **Budget Utilization**: Percentage of allocated budget used
- **Cost Trends**: Monthly spending patterns and projections
- **ROI Indicators**: Value generated vs. resources consumed

## Dashboard Data Sources

### MLflow Integration
- Experiment tracking and model performance
- Cost calculation data from backend utilities
- Agent interaction logs and metrics
- Quality scores and user feedback

### Database Queries
- Project metadata and status information
- User activity logs and session data
- Generated file inventory and metadata
- Agent performance and error logs

### Real-time Updates
- WebSocket connections for live project status
- Server-sent events for notifications
- Periodic polling for non-critical metrics
- Background sync for data consistency

## User Interactions

### Navigation Patterns
1. **Dashboard** → View project card → **Task Execution View**
2. **Dashboard** → File link → **Document viewer/download**
3. **Dashboard** → Metrics widget → **Detailed analytics page**
4. **Dashboard** → Suggestion → **New analysis wizard**
5. **Dashboard** → Recent activity → **Activity detail view**

### Quick Actions
- **Start New Analysis**: Launch analysis wizard with templates
- **View All Projects**: Navigate to comprehensive project list
- **Export Reports**: Bulk download of selected project outputs
- **System Settings**: Access configuration and preferences
- **Help & Support**: Documentation, tutorials, and contact options

## Responsive Design Considerations

### Desktop (1920x1080+)
- Full three-column layout with detailed widgets
- Expanded charts and visualizations
- Maximum information density

### Tablet (768x1024)
- Two-column layout (merge right column into center)
- Collapsible sidebar navigation
- Touch-optimized buttons and interactions

### Mobile (375x667)
- Single column stack layout
- Hamburger menu navigation
- Swipe gestures for cards and lists
- Simplified metrics display

## Implementation Priority

### Phase 1: Core Dashboard
1. Project overview cards with basic status
2. Simple activity timeline
3. Key metrics widgets (counts, costs, scores)
4. Navigation to Task Execution view

### Phase 2: Analytics & Insights
1. Detailed performance metrics and charts
2. AI-generated insights and suggestions
3. Advanced filtering and search capabilities
4. File management browser

### Phase 3: Advanced Features
1. Customizable dashboard layouts
2. Real-time collaboration features
3. Advanced analytics and reporting
4. Integration with external tools and APIs

## Technical Requirements

### Frontend Components
- **DashboardHome.tsx**: Main dashboard page component
- **ProjectCard.tsx**: Individual project status cards
- **MetricsWidget.tsx**: Reusable metrics display components
- **ActivityTimeline.tsx**: Activity feed with filtering
- **FileExplorer.tsx**: File management interface
- **SuggestionsPanel.tsx**: AI recommendations display

### API Endpoints Needed
- `GET /api/dashboard/overview` - Main dashboard data
- `GET /api/projects/summary` - Project cards data
- `GET /api/metrics/summary` - Key performance indicators
- `GET /api/activity/recent` - Activity timeline data
- `GET /api/files/recent` - Recent files and documents
- `GET /api/suggestions/latest` - AI-generated recommendations

### Data Refresh Strategy
- **Real-time**: Project status, active agent states
- **30 seconds**: Activity timeline, notifications
- **5 minutes**: Metrics, file listings
- **1 hour**: Analytics, trends, suggestions
- **Manual**: User-triggered refresh for specific widgets

This dashboard design provides users with comprehensive oversight of their ATLAS system while maintaining the clean, professional aesthetic established in the Task Execution interface.
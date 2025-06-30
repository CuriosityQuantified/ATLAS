# ATLAS Frontend

A modern Next.js dashboard for the ATLAS multi-agent system with dark theme and glassmorphism design.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000 in your browser
```

## Features

### Current Implementation: Task Execution Interface
- **Dark Theme**: Sophisticated dark design with glassmorphism effects
- **Agent Visualization**: Hierarchical multi-agent status display
- **Real-time Updates**: Live agent progress and status monitoring
- **Responsive Design**: Works on desktop, tablet, and mobile
- **TypeScript**: Full type safety throughout

### Planned: Dashboard Interface
The current interface is the **Task Execution View** - the active workspace where users monitor live agent activities during analysis tasks.

A separate **Dashboard View** will serve as the homepage, featuring:
- **Project Overview**: Cards showing all active and completed projects
- **Metrics Dashboard**: Cost tracking, completion rates, quality scores
- **Recent Activity**: Timeline of tasks and agent activities
- **File Management**: Links to generated reports, documents, and artifacts
- **Quick Actions**: Start new analysis, access settings, view reports
- **Suggestions Engine**: AI-generated next steps and project recommendations
- **Analytics**: Usage patterns, agent performance trends, resource utilization

## Design System

### Color Palette
- **Background**: #0f172a (Dark slate)
- **Primary**: #2563eb (Blue)
- **Accent**: #f59e42 (Orange)
- **Status Colors**: Green (active), Orange (processing), Gray (idle)

### Layout (Task Execution View)
- **Left Sidebar**: Navigation and user profile
- **Main Area**: Live agent architecture grid with status indicators
- **Right Panel**: Agent questions and real-time notifications
- **Bottom Chat**: Direct communication with active agents

### Planned Layout (Dashboard View)
- **Header**: Global navigation, user profile, notifications
- **Main Grid**: Project cards, metrics widgets, recent activity
- **Sidebar**: Quick actions, suggestions, file browser
- **Footer**: System status, version info, help links

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Heroicons
- **Font**: Inter (Google Fonts)

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main dashboard page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── Dashboard.tsx      # Main layout
│   ├── Sidebar.tsx        # Left navigation
│   ├── AgentArchitecture.tsx # Agent grid
│   ├── AgentCard.tsx      # Individual agent cards
│   ├── QuestionsPanel.tsx # Right sidebar
│   └── ChatBar.tsx        # Bottom chat
└── types/                 # TypeScript definitions
    └── index.ts           # Shared types
```

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

## Design Reference

The original design prototype is preserved in `reference-design/`:
- `index.html` - Complete HTML structure
- `style.css` - Original CSS with glassmorphism effects
- `app.js` - Vanilla JavaScript interactions

These files serve as the design source of truth and should be maintained for consistency.

## Required Dependencies

All dependencies are automatically installed with `npm install`:

### Runtime Dependencies
- `next` - Next.js framework
- `react` & `react-dom` - React library
- `@heroicons/react` - Icon library
- `clsx` - Conditional CSS classes
- `tailwind-merge` - Tailwind CSS utility merging

### Development Dependencies  
- `typescript` - TypeScript compiler
- `@types/*` - TypeScript definitions
- `tailwindcss` - CSS framework
- `autoprefixer` - CSS post-processor
- `postcss` - CSS transformer
- `eslint` - Code linting

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+

## Contributing

1. Follow the existing design system and component patterns
2. Maintain TypeScript type safety
3. Use Tailwind CSS classes for styling
4. Test responsive design across screen sizes
5. Keep components focused and reusable
'use client';

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function CopilotProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Configure CopilotKit to connect to our AG-UI backend
  const runtimeUrl = process.env.NEXT_PUBLIC_COPILOT_RUNTIME_URL || "/api/copilotkit";

  return (
    <CopilotKit
      runtimeUrl={runtimeUrl}
      headers={{
        // Add any authentication headers if needed
        "X-Task-ID": "default", // This will be dynamic in production
      }}
    >
      <CopilotSidebar
        labels={{
          title: "ATLAS Assistant",
          initial: "How can I help you with your analysis task today?",
        }}
        defaultOpen={false}
        clickOutsideToClose={false}
      >
        {children}
      </CopilotSidebar>
    </CopilotKit>
  );
}
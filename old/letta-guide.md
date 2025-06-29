


# 🛠️ Built-in Coordination Tools - Detailed Implementation Analysis

Based on my analysis of the Letta codebase, here's how each coordination ability works with detailed technical implementation:

## 1. Asynchronous Messaging (`send_message_to_agent_async`)

This tool enables fire-and-forget messaging between agents, similar to modern messaging platforms where you send a message and get a delivery receipt without waiting for a reply.

### Implementation Architecture:
- **Function Definition**: The tool is defined as a standard Python function with string parameters for `message` and `other_agent_id` [1](#0-0) 
- **Executor Implementation**: The `LettaMultiAgentToolExecutor` class handles the actual execution using an asynchronous task creation pattern [2](#0-1) 
- **Task Management**: Uses `asyncio.create_task()` to spawn background processing for the target agent, allowing the sender to continue immediately
- **Message Augmentation**: Automatically adds sender information to the message before delivery using helper functions [3](#0-2) 

### Key Libraries and Imports:
The implementation relies on Python's asyncio library for non-blocking execution, Pydantic schemas for message validation, and Letta's internal agent management system for agent lookup and message processing.

## 2. Synchronous Messaging (`send_message_to_agent_and_wait_for_reply`)

This tool implements request-response patterns where the sending agent pauses execution until receiving a reply from the target agent.

### Implementation Architecture:
- **Function Definition**: Defined with the same parameter signature as async messaging but with blocking execution semantics [4](#0-3) 
- **Executor Implementation**: The `LettaMultiAgentToolExecutor` implements synchronous execution by directly calling the `_process_agent` helper method [5](#0-4) 
- **Agent Processing**: Creates a new `LettaAgent` instance for the target agent and executes a single step with the incoming message
- **Response Handling**: Waits for the target agent's complete response before returning to the sender

### Execution Flow:
The tool uses Letta's core agent execution pipeline, instantiating the target agent, processing the message through its reasoning system, and capturing the full response for synchronous return.

## 3. Supervisor-Worker Broadcast (`send_message_to_agents_matching_tags`)

This tool enables hierarchical coordination where a supervisor agent can broadcast messages to multiple worker agents based on tag-based filtering.

### Implementation Architecture:
- **Function Definition**: Takes message content plus tag matching parameters (`match_all` and `match_some` lists) [6](#0-5) 
- **Tag-Based Discovery**: Uses the `AgentManager.list_agents_matching_tags_async()` method to find agents matching the specified tag criteria [7](#0-6) 
- **Parallel Execution**: Broadcasts messages to all matching agents concurrently and collects responses
- **Response Aggregation**: Combines all worker responses into a structured result for the supervisor

### Coordination Patterns Implementation:

#### Core Multi-Agent Tools Registration:
All three tools are registered as part of the `MULTI_AGENT_TOOLS` constant and automatically made available to agents when multi-agent functionality is enabled [8](#0-7) 

#### Tool Execution Pipeline:
The execution flow follows Letta's standard tool execution pattern:
1. **Tool Call Recognition**: Agent's LLM generates tool calls during reasoning
2. **Factory Dispatch**: `ToolExecutorFactory` routes multi-agent tools to `LettaMultiAgentToolExecutor` [9](#0-8) 
3. **Function Mapping**: Executor maps tool names to implementation methods
4. **Agent Processing**: Core `_process_agent` helper manages target agent lifecycle [10](#0-9) 

## 🔗 Coordination Patterns Implementation

### 1. Decentralized Peer-to-Peer
**Implementation**: Agents are created with multi-agent tools attached directly through the Agent Development Environment or SDK. Each agent maintains independent memory and can initiate communication with any other agent by ID [11](#0-10) 

### 2. Supervisor-Worker Hierarchy
**Implementation**: 
- **Supervisor Creation**: Supervisor agents are configured with broadcast tools and given management tags [12](#0-11) 
- **Worker Registration**: Worker agents are created with specific tags that identify their capabilities or group membership
- **Shared State**: Workers can share state through core memory blocks linked by ID across multiple agents
- **Task Distribution**: Uses tag-based filtering to route tasks to appropriate worker subsets

### 3. Custom Hybrid Workflows
**Implementation**: The system supports complex orchestration by combining async triggers with sync responses. For example, a supervisor can async-trigger multiple workers and then use sync calls to collect specific results, all while maintaining shared context through:
- **Core Memory Blocks**: Editable in-context memory shared across agents via block IDs
- **Archival Memory**: Centralized vector database accessible to all agents for cross-agent data retrieval

## ⚙️ Implementation Highlights

### State Persistence
Each agent maintains completely independent memory systems (conversation history, core memory blocks) while supporting shared memory constructs for coordination [13](#0-12) 

### Transparency and Observability
All multi-agent interactions, including reasoning steps and tool usage, are visible through the Agent Development Environment, providing complete audit trails of inter-agent communication.

### Scalability Architecture
The system is designed for Docker-compatible deployment with async task management enabling horizontal scaling of multi-agent workflows across distributed infrastructure.

The coordination tools provide granular control over agent interactions while maintaining the balance between autonomous agent behavior and structured coordination patterns essential for complex multi-agent systems.

## Notes

The implementation uses a sophisticated executor pattern where multi-agent tools are treated as first-class citizens in Letta's tool system. The `LettaMultiAgentToolExecutor` handles the complexity of agent-to-agent communication while maintaining each agent's independence and memory isolation. All coordination happens through well-defined tool interfaces that can be mixed and matched to create complex multi-agent workflows.

These instructs are for Next.js setups with the app router
<for Next.js>
1. Install the Letta SDK and Vercel's AI packages

npm

yarn

pnpm
npm install -s @letta-ai/vercel-ai-sdk-provider ai @ai-sdk/react

Copy
2. Create or append a .env.local file at the root of your application, and add the following environment values:
LETTA_API_KEY=YOUR_API_KEY
LETTA_DEFAULT_PROJECT_SLUG=default-project
LETTA_DEFAULT_TEMPLATE_NAME=great-yellow-shark:latest

Show API Key


Download

Copy
3. Create a file at /api/chat/route.ts, this endpoint will be used to stream messages back via an agentId
Code
import { streamText } from 'ai';
import { lettaCloud } from '@letta-ai/vercel-ai-sdk-provider';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
    const { messages, agentId } = await req.json();

    if (!agentId) {
        throw new Error('Missing agentId');
    }

    const result = streamText({
        model: lettaCloud(agentId),
        messages,
    });

    return result.toDataStreamResponse();
}



Download

Copy
4. Create a client-component called <Chat/> that will be used to chat with the agent
Code
'use client';

import {useChat} from '@ai-sdk/react';
import {useEffect, useMemo, useRef} from "react";
import {Message} from "@ai-sdk/ui-utils";

interface ChatProps {
    agentId: string
    existingMessages: Message[]
    saveAgentIdCookie: (agentId: string) => void
}

export function Chat(props: ChatProps) {
    const {agentId, existingMessages, saveAgentIdCookie} = props;

    const agentIdSaved = useRef<boolean>(false);

    useEffect(() => {
        if (agentIdSaved.current) {
            return;
        }

        agentIdSaved.current = true;
        saveAgentIdCookie(agentId);
    }, [agentId, saveAgentIdCookie]);


    const {messages, status, input, handleInputChange, handleSubmit} = useChat({
        body: {agentId},
        initialMessages: existingMessages,
    });

    const isLoading = useMemo(() => {
        return status === 'streaming' || status === 'submitted'
    }, [status]);

    return (
        <div className="flex flex-col w-full max-w-md py-24 mx-auto stretch">
            <div>Chatting with {agentId}</div>
            {messages.map(message => (
                <div key={message.id} className="whitespace-pre-wrap">
                    {message.role === 'user' ? 'User: ' : 'AI: '}
                    {message.parts.map((part, i) => {
                        switch (part.type) {
                            case 'text':
                                return <div key={message.id}>{part.text}</div>;
                        }
                    })}
                </div>
            ))}

            <form onSubmit={handleSubmit}>
                {isLoading && (
                    <div className="flex items-center justify-center w-full h-12">
                        Streaming...
                    </div>
                )}
                <input
                    className="fixed dark:bg-zinc-900 bottom-0 w-full max-w-md p-2 mb-8 border border-zinc-300 dark:border-zinc-800 rounded shadow-xl"
                    value={input}
                    disabled={status !== 'ready'}
                    placeholder="Say something..."
                    onChange={handleInputChange}
                />
            </form>
        </div>
    );
}
</for Next.js>

These instructions are for Python
<for python>
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)

# create agent
response = client.templates.agents.create(
    project="default-project",
    template_version="great-yellow-shark:latest",
)

# message agent
client.agents.messages.create(
    agent_id=response.agents[0].id,
    messages=[{"role": "user", "content": "hello"}],
</for python>
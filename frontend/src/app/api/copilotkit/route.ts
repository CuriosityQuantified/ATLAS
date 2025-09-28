import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Get the task ID from headers or generate one
    const taskId = request.headers.get('X-Task-ID') || 'default';

    // Forward the request to our backend AG-UI bridge
    const response = await fetch(`${BACKEND_URL}/api/copilotkit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Task-ID': taskId,
      },
      body: JSON.stringify(await request.json()),
    });

    // Stream the response back to CopilotKit
    if (response.headers.get('content-type')?.includes('text/event-stream')) {
      // Handle SSE streaming
      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }

    // Handle regular JSON responses
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with backend' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const path = url.pathname.replace('/api/copilotkit', '');

    // Forward GET requests (like status checks)
    const response = await fetch(`${BACKEND_URL}/api/copilotkit${path}`, {
      method: 'GET',
      headers: {
        'X-Task-ID': request.headers.get('X-Task-ID') || 'default',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with backend' },
      { status: 500 }
    );
  }
}
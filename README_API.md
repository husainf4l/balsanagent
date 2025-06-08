# FastAPI Chat Agent

This FastAPI application provides REST API endpoints for the AI Business Advisor chat agent, designed to be consumed by a Next.js frontend.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure your environment variables are set (in `.env` file):

```
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgresql_connection_string
```

3. Run the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check

- **GET** `/health`
- Returns server health status

### Create Session

- **POST** `/api/sessions`
- Body: `{"session_id": "optional_existing_id"}` (optional)
- Returns: `{"session_id": "uuid"}`

### Send Chat Message

- **POST** `/api/chat`
- Body: `{"message": "your message", "session_id": "optional_session_id"}`
- Returns: `{"response": "agent response", "session_id": "uuid", "error": null, "tokens_used": 123}`

### Get Chat History

- **GET** `/api/sessions/{session_id}/history`
- Returns: `{"session_id": "uuid", "history": [{"role": "user", "content": "message", "timestamp": ""}]}`

### Clear Session

- **DELETE** `/api/sessions/{session_id}`
- Returns: `{"session_id": "new_uuid"}`

## CORS Configuration

The API is configured to accept requests from:

- `http://localhost:3000` (Next.js dev server)
- `http://localhost:3001`
- Add your production domains in `main.py`

## Next.js Integration Example

```typescript
// api/chat.ts
const API_BASE_URL = "http://localhost:8000";

export interface ChatMessage {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  error?: string;
  tokens_used?: number;
}

export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function createSession(): Promise<{ session_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function getChatHistory(sessionId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/history`
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
```

## React Component Example

```typescript
// components/ChatInterface.tsx
import React, { useState, useEffect } from "react";
import { sendMessage, createSession, ChatResponse } from "../api/chat";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Create a new session when component mounts
    const initSession = async () => {
      try {
        const session = await createSession();
        setSessionId(session.session_id);
      } catch (error) {
        console.error("Failed to create session:", error);
      }
    };

    initSession();
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    setLoading(true);

    // Add user message to UI
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const response: ChatResponse = await sendMessage(userMessage, sessionId);

      if (response.error) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${response.error}`,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: response.response,
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Network error: ${error}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
        {loading && <div className="loading">Agent is thinking...</div>}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask me about your business data..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
```

## Interactive Testing

You can test the API using the interactive documentation at:
`http://localhost:8000/docs`

Or using curl:

```bash
# Create a session
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json"

# Send a message
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are our top products by sales?", "session_id": "your-session-id"}'

# Get chat history
curl -X GET "http://localhost:8000/api/sessions/your-session-id/history"
```

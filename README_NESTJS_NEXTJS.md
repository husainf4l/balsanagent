# NestJS + Next.js Integration with FastAPI Chat Agent

This guide shows how to integrate your FastAPI AI Business Advisor with a NestJS backend and Next.js frontend.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │    NestJS       │    │   FastAPI       │
│   Frontend      │◄──►│   Backend       │◄──►│   AI Agent      │
│   (Port 3000)   │    │   (Port 3001)   │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Benefits of this architecture:**

- 🔒 **Security**: NestJS can handle authentication, rate limiting, and API key management
- 🛡️ **Validation**: Additional request/response validation layer
- 📊 **Monitoring**: Centralized logging, metrics, and request tracking
- 🔄 **Caching**: Response caching for improved performance
- 🌐 **API Gateway**: Single entry point for multiple services
- 🎯 **Business Logic**: Custom business rules and data transformation

## NestJS Backend Setup

### 1. Create NestJS Project

```bash
# Install NestJS CLI
npm i -g @nestjs/cli

# Create new project
nest new ai-chat-backend
cd ai-chat-backend

# Install additional dependencies
npm install @nestjs/config @nestjs/throttler axios class-validator class-transformer
npm install --save-dev @types/node
```

### 2. NestJS Project Structure

```
src/
├── app.module.ts
├── main.ts
├── chat/
│   ├── chat.module.ts
│   ├── chat.controller.ts
│   ├── chat.service.ts
│   └── dto/
│       ├── chat-message.dto.ts
│       ├── chat-response.dto.ts
│       └── session.dto.ts
├── common/
│   ├── guards/
│   │   └── auth.guard.ts
│   ├── interceptors/
│   │   └── logging.interceptor.ts
│   └── filters/
│       └── http-exception.filter.ts
└── config/
    └── configuration.ts
```

### 3. Environment Configuration

Create `.env` file:

```env
# NestJS Configuration
PORT=3001
NODE_ENV=development

# FastAPI Chat Agent
FASTAPI_BASE_URL=http://localhost:8000

# Rate Limiting
THROTTLE_TTL=60
THROTTLE_LIMIT=100

# Optional: Authentication
JWT_SECRET=your-jwt-secret
API_KEY=your-api-key
```

### 4. NestJS Implementation Files

#### `src/config/configuration.ts`

```typescript
export default () => ({
  port: parseInt(process.env.PORT, 10) || 3001,
  fastapi: {
    baseUrl: process.env.FASTAPI_BASE_URL || "http://localhost:8000",
  },
  throttle: {
    ttl: parseInt(process.env.THROTTLE_TTL, 10) || 60,
    limit: parseInt(process.env.THROTTLE_LIMIT, 10) || 100,
  },
});
```

#### `src/chat/dto/chat-message.dto.ts`

```typescript
import { IsString, IsOptional, IsNotEmpty, MaxLength } from "class-validator";

export class ChatMessageDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(2000)
  message: string;

  @IsOptional()
  @IsString()
  session_id?: string;
}

export class SessionDto {
  @IsOptional()
  @IsString()
  session_id?: string;
}

export class ChatResponseDto {
  response: string;
  session_id: string;
  error?: string;
  tokens_used?: number;
  timestamp: string;
}
```

#### `src/chat/chat.service.ts`

```typescript
import { Injectable, HttpException, HttpStatus, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import axios, { AxiosResponse } from "axios";
import {
  ChatMessageDto,
  ChatResponseDto,
  SessionDto,
} from "./dto/chat-message.dto";

@Injectable()
export class ChatService {
  private readonly logger = new Logger(ChatService.name);
  private readonly fastApiUrl: string;

  constructor(private configService: ConfigService) {
    this.fastApiUrl = this.configService.get<string>("fastapi.baseUrl");
  }

  async createSession(
    sessionDto?: SessionDto
  ): Promise<{ session_id: string }> {
    try {
      this.logger.log("Creating new chat session");

      const response: AxiosResponse = await axios.post(
        `${this.fastApiUrl}/api/sessions`,
        sessionDto,
        {
          headers: { "Content-Type": "application/json" },
          timeout: 10000,
        }
      );

      return response.data;
    } catch (error) {
      this.logger.error(
        "Failed to create session",
        error.response?.data || error.message
      );
      throw new HttpException(
        "Failed to create chat session",
        HttpStatus.SERVICE_UNAVAILABLE
      );
    }
  }

  async sendMessage(chatMessageDto: ChatMessageDto): Promise<ChatResponseDto> {
    try {
      this.logger.log(
        `Sending message: ${chatMessageDto.message.substring(0, 50)}...`
      );

      const response: AxiosResponse = await axios.post(
        `${this.fastApiUrl}/api/chat`,
        chatMessageDto,
        {
          headers: { "Content-Type": "application/json" },
          timeout: 30000, // AI responses can take longer
        }
      );

      const result = {
        ...response.data,
        timestamp: new Date().toISOString(),
      };

      this.logger.log("Message processed successfully");
      return result;
    } catch (error) {
      this.logger.error(
        "Failed to send message",
        error.response?.data || error.message
      );
      throw new HttpException(
        "Failed to process chat message",
        HttpStatus.SERVICE_UNAVAILABLE
      );
    }
  }

  // 🚀 NEW: Streaming message support
  async *streamMessage(
    chatMessageDto: ChatMessageDto
  ): AsyncGenerator<string, void, unknown> {
    try {
      this.logger.log(
        `Streaming message: ${chatMessageDto.message.substring(0, 50)}...`
      );

      const response = await axios.post(
        `${this.fastApiUrl}/api/chat/stream`,
        chatMessageDto,
        {
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          responseType: "stream",
          timeout: 60000, // Longer timeout for streaming
        }
      );

      // Parse Server-Sent Events
      for await (const chunk of response.data) {
        const lines = chunk.toString().split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data && data !== "[DONE]") {
              yield data;
            }
          }
        }
      }

      this.logger.log("Streaming completed successfully");
    } catch (error) {
      this.logger.error(
        "Failed to stream message",
        error.response?.data || error.message
      );
      throw new HttpException(
        "Failed to stream chat message",
        HttpStatus.SERVICE_UNAVAILABLE
      );
    }
  }

  async getChatHistory(sessionId: string): Promise<any> {
    try {
      this.logger.log(`Retrieving history for session: ${sessionId}`);

      const response: AxiosResponse = await axios.get(
        `${this.fastApiUrl}/api/sessions/${sessionId}/history`,
        { timeout: 10000 }
      );

      return response.data;
    } catch (error) {
      this.logger.error(
        "Failed to get chat history",
        error.response?.data || error.message
      );
      throw new HttpException(
        "Failed to retrieve chat history",
        HttpStatus.SERVICE_UNAVAILABLE
      );
    }
  }

  async clearSession(sessionId: string): Promise<{ session_id: string }> {
    try {
      this.logger.log(`Clearing session: ${sessionId}`);

      const response: AxiosResponse = await axios.delete(
        `${this.fastApiUrl}/api/sessions/${sessionId}`,
        { timeout: 10000 }
      );

      return response.data;
    } catch (error) {
      this.logger.error(
        "Failed to clear session",
        error.response?.data || error.message
      );
      throw new HttpException(
        "Failed to clear chat session",
        HttpStatus.SERVICE_UNAVAILABLE
      );
    }
  }

  async checkHealth(): Promise<{ status: string; fastapi: boolean }> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.fastApiUrl}/health`,
        { timeout: 5000 }
      );

      return {
        status: "healthy",
        fastapi: response.status === 200,
      };
    } catch (error) {
      this.logger.error("Health check failed", error.message);
      return {
        status: "unhealthy",
        fastapi: false,
      };
    }
  }
}
```

#### `src/chat/chat.controller.ts`

```typescript
import {
  Controller,
  Get,
  Post,
  Delete,
  Body,
  Param,
  HttpCode,
  HttpStatus,
  UseGuards,
  UseInterceptors,
  Res,
} from "@nestjs/common";
import { ThrottlerGuard } from "@nestjs/throttler";
import { Response } from "express";
import { ChatService } from "./chat.service";
import { ChatMessageDto, SessionDto } from "./dto/chat-message.dto";
import { LoggingInterceptor } from "../common/interceptors/logging.interceptor";

@Controller("api")
@UseGuards(ThrottlerGuard)
@UseInterceptors(LoggingInterceptor)
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Get("health")
  @HttpCode(HttpStatus.OK)
  async health() {
    return this.chatService.checkHealth();
  }

  @Post("sessions")
  @HttpCode(HttpStatus.CREATED)
  async createSession(@Body() sessionDto?: SessionDto) {
    return this.chatService.createSession(sessionDto);
  }

  @Post("chat")
  @HttpCode(HttpStatus.OK)
  async sendMessage(@Body() chatMessageDto: ChatMessageDto) {
    return this.chatService.sendMessage(chatMessageDto);
  }

  // 🚀 NEW: Streaming chat endpoint
  @Post("chat/stream")
  async streamMessage(
    @Body() chatMessageDto: ChatMessageDto,
    @Res() res: Response
  ) {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Headers", "*");

    try {
      for await (const chunk of this.chatService.streamMessage(
        chatMessageDto
      )) {
        res.write(`data: ${chunk}\n\n`);
      }
      res.write(`data: {"type": "done"}\n\n`);
    } catch (error) {
      res.write(`data: {"error": "${error.message}", "type": "error"}\n\n`);
    } finally {
      res.end();
    }
  }

  @Get("sessions/:sessionId/history")
  @HttpCode(HttpStatus.OK)
  async getChatHistory(@Param("sessionId") sessionId: string) {
    return this.chatService.getChatHistory(sessionId);
  }

  @Delete("sessions/:sessionId")
  @HttpCode(HttpStatus.OK)
  async clearSession(@Param("sessionId") sessionId: string) {
    return this.chatService.clearSession(sessionId);
  }
}
```

#### `src/chat/chat.module.ts`

```typescript
import { Module } from "@nestjs/common";
import { ChatController } from "./chat.controller";
import { ChatService } from "./chat.service";

@Module({
  controllers: [ChatController],
  providers: [ChatService],
})
export class ChatModule {}
```

#### `src/common/interceptors/logging.interceptor.ts`

```typescript
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from "@nestjs/common";
import { Observable } from "rxjs";
import { tap } from "rxjs/operators";

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url, body } = request;
    const now = Date.now();

    this.logger.log(`${method} ${url} - Request started`);

    return next.handle().pipe(
      tap(() => {
        const responseTime = Date.now() - now;
        this.logger.log(`${method} ${url} - Completed in ${responseTime}ms`);
      })
    );
  }
}
```

#### `src/app.module.ts`

```typescript
import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { ThrottlerModule } from "@nestjs/throttler";
import configuration from "./config/configuration";
import { ChatModule } from "./chat/chat.module";

@Module({
  imports: [
    ConfigModule.forRoot({
      load: [configuration],
      isGlobal: true,
    }),
    ThrottlerModule.forRootAsync({
      useFactory: () => ({
        throttlers: [
          {
            ttl: parseInt(process.env.THROTTLE_TTL, 10) || 60,
            limit: parseInt(process.env.THROTTLE_LIMIT, 10) || 100,
          },
        ],
      }),
    }),
    ChatModule,
  ],
})
export class AppModule {}
```

#### `src/main.ts`

```typescript
import { NestFactory } from "@nestjs/core";
import { ValidationPipe } from "@nestjs/common";
import { AppModule } from "./app.module";

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Enable CORS for Next.js
  app.enableCors({
    origin: [
      "http://localhost:3000",
      "http://localhost:3001",
      "https://yourdomain.com",
    ],
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    credentials: true,
  });

  // Global validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    })
  );

  const port = process.env.PORT || 3001;
  await app.listen(port);
  console.log(`🚀 NestJS server running on http://localhost:${port}`);
}
bootstrap();
```

## Next.js Frontend Setup

### 1. Updated API Client for NestJS with Streaming Support

Create `lib/chat-api.ts`:

```typescript
// lib/chat-api.ts
// API client for the NestJS backend with streaming support

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

export interface ChatMessage {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  error?: string;
  tokens_used?: number;
  timestamp: string;
}

export interface SessionResponse {
  session_id: string;
}

export interface HistoryResponse {
  session_id: string;
  history: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
}

export interface StreamChunk {
  content?: string;
  type: "session" | "content" | "done" | "error";
  session_id?: string;
  index?: number;
  error?: string;
}

class ChatApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ChatApiError";
  }
}

// Regular API functions
export async function createSession(
  existingSessionId?: string
): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: existingSessionId
      ? JSON.stringify({ session_id: existingSessionId })
      : undefined,
  });

  if (!response.ok) {
    throw new ChatApiError(
      response.status,
      `Failed to create session: ${response.statusText}`
    );
  }

  return await response.json();
}

export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new ChatApiError(
      response.status,
      `Failed to send message: ${response.statusText}`
    );
  }

  return await response.json();
}

// 🚀 NEW: Streaming message function
export async function* streamMessage(
  message: string,
  sessionId?: string
): AsyncGenerator<StreamChunk, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new ChatApiError(
      response.status,
      `Failed to stream message: ${response.statusText}`
    );
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new ChatApiError(500, "No response body reader available");
  }

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data.trim()) {
            try {
              const parsed: StreamChunk = JSON.parse(data);
              yield parsed;

              if (parsed.type === "done" || parsed.type === "error") {
                return;
              }
            } catch (e) {
              console.warn("Failed to parse streaming data:", data);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function getChatHistory(
  sessionId: string
): Promise<HistoryResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/history`
  );

  if (!response.ok) {
    throw new ChatApiError(
      response.status,
      `Failed to get chat history: ${response.statusText}`
    );
  }

  return await response.json();
}

export async function clearSession(
  sessionId: string
): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new ChatApiError(
      response.status,
      `Failed to clear session: ${response.statusText}`
    );
  }

  return await response.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}
```

### 2. Next.js Environment Configuration

Create `.env.local`:

```env
# Next.js Configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### 3. Usage in Next.js Pages

```typescript
// pages/chat.tsx or app/chat/page.tsx
import { useState, useEffect } from "react";
import { sendMessage, createSession, ChatResponse } from "../lib/chat-api";

export default function ChatPage() {
  const [messages, setMessages] = useState<
    Array<{ role: string; content: string }>
  >([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize session
    createSession().then((session) => {
      setSessionId(session.session_id);
    });
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: input }]);

    try {
      const response: ChatResponse = await sendMessage(input, sessionId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.response },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "error", content: "Failed to send message" },
      ]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about your business data..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
```

### 3. Streaming Chat Component for Next.js

```typescript
// components/StreamingChatInterface.tsx
import { useState, useEffect, useRef } from "react";
import {
  sendMessage,
  createSession,
  streamMessage,
  ChatResponse,
  StreamChunk,
} from "../lib/chat-api";

interface Message {
  role: "user" | "assistant" | "error";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export default function StreamingChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize session
    createSession().then((session) => {
      setSessionId(session.session_id);
    });
  }, []);

  const handleStreamingSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setInput("");

    // Create placeholder for streaming message
    const assistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      let streamedContent = "";
      let currentSessionId = sessionId;

      for await (const chunk of streamMessage(input, sessionId)) {
        if (chunk.type === "session" && chunk.session_id) {
          currentSessionId = chunk.session_id;
          setSessionId(chunk.session_id);
        } else if (chunk.type === "content" && chunk.content) {
          streamedContent += chunk.content + " ";

          // Update the streaming message
          setMessages((prev) =>
            prev.map((msg, index) =>
              index === prev.length - 1
                ? { ...msg, content: streamedContent.trim() }
                : msg
            )
          );
        } else if (chunk.type === "error") {
          setMessages((prev) =>
            prev.map((msg, index) =>
              index === prev.length - 1
                ? {
                    ...msg,
                    content: `Error: ${chunk.error}`,
                    role: "error",
                    isStreaming: false,
                  }
                : msg
            )
          );
          break;
        } else if (chunk.type === "done") {
          // Mark streaming as complete
          setMessages((prev) =>
            prev.map((msg, index) =>
              index === prev.length - 1 ? { ...msg, isStreaming: false } : msg
            )
          );
          break;
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      setMessages((prev) =>
        prev.map((msg, index) =>
          index === prev.length - 1
            ? {
                ...msg,
                content: "Failed to stream message",
                role: "error",
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRegularSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response: ChatResponse = await sendMessage(input, sessionId);

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      const assistantMessage: Message = {
        role: response.error ? "error" : "assistant",
        content: response.error || response.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        role: "error",
        content: "Failed to send message",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  const handleSend = () => {
    if (useStreaming) {
      handleStreamingSend();
    } else {
      handleRegularSend();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">AI Business Advisor</h1>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Streaming Mode</span>
          </label>
          <span className="text-xs bg-blue-700 px-2 py-1 rounded">
            Session: {sessionId.slice(-8)}
          </span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p>Welcome to your AI Business Advisor!</p>
            <p className="text-sm mt-2">
              {useStreaming
                ? "Streaming mode enabled - responses will appear word by word"
                : "Regular mode - full responses at once"}
            </p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-500 text-white"
                  : msg.role === "error"
                  ? "bg-red-100 text-red-800 border border-red-300"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
              {msg.isStreaming && (
                <div className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></div>
              )}
              <div className="text-xs opacity-70 mt-1">
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your business data..."
            disabled={loading}
            className="flex-1 p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              loading || !input.trim()
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-blue-500 text-white hover:bg-blue-600"
            }`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                {useStreaming ? "Streaming..." : "Sending..."}
              </div>
            ) : (
              "Send"
            )}
          </button>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Press Enter to send • Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}
```

## Streaming Implementation Guide

### Overview

This implementation provides both regular and streaming chat modes:

- **Regular Mode**: Traditional request-response with full messages
- **Streaming Mode**: Real-time word-by-word streaming using Server-Sent Events (SSE)

### Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │    NestJS       │    │   FastAPI       │
│   SSE Client    │◄──►│   SSE Proxy     │◄──►│   SSE Server    │
│   (EventSource) │    │   (Stream Parse)│    │   (AsyncGen)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### FastAPI Streaming Server

The streaming server is implemented in `main_streaming.py`:

**Key Features:**

- Word-by-word streaming with configurable delays
- Server-Sent Events (SSE) format
- Proper CORS headers for cross-origin requests
- Error handling with graceful fallback
- Session management for conversation context

**Streaming Endpoint:**

```bash
POST /api/chat/stream
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Event Format:**

```
data: {"type": "word", "content": "Hello"}

data: {"type": "word", "content": "world"}

data: {"type": "done"}
```

### NestJS Streaming Integration

The NestJS backend acts as a proxy between Next.js and FastAPI:

**Features:**

- Async generator for stream processing
- SSE event parsing and validation
- Error handling and reconnection logic
- Session state management
- Request logging and monitoring

**Implementation Highlights:**

```typescript
async *streamMessage(message: string, sessionId?: string) {
  // Parse SSE stream from FastAPI
  // Validate and transform events
  // Handle errors gracefully
  // Yield processed chunks
}
```

### Next.js Frontend Integration

The React component provides a seamless streaming experience:

**Features:**

- Toggle between streaming and regular modes
- Real-time word-by-word display
- Typing indicators and visual feedback
- Error handling with user notifications
- Responsive design with modern UI

**User Experience:**

- ✅ Smooth toggle between modes
- ✅ Real-time message updates
- ✅ Loading states and indicators
- ✅ Error handling with recovery
- ✅ Mobile-friendly interface

### Testing Streaming Functionality

#### Manual Testing

1. **Start all services** (see Deployment section below)

2. **Test streaming endpoint directly:**

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about business analytics", "session_id": "test-123"}' \
  --no-buffer
```

3. **Test through NestJS proxy:**

```bash
curl -X POST http://localhost:3001/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the key metrics for my business?"}' \
  --no-buffer
```

4. **Test in browser:**
   - Open http://localhost:3000
   - Toggle "Enable Streaming" switch
   - Send a message and watch real-time streaming

#### Automated Testing

The test script validates all components:

```bash
# Run comprehensive streaming tests
chmod +x test_streaming.sh
./test_streaming.sh
```

**Test Coverage:**

- ✅ FastAPI streaming endpoint functionality
- ✅ NestJS proxy and SSE parsing
- ✅ Next.js EventSource integration
- ✅ Error handling and recovery
- ✅ Session management across streams
- ✅ Performance and memory usage
- ✅ Concurrent streaming sessions

### Troubleshooting

#### Common Issues

**1. Streaming not working in browser**

```bash
# Check CORS headers
curl -I http://localhost:8000/api/chat/stream
# Should include: Access-Control-Allow-Origin: *
```

**2. EventSource connection errors**

```javascript
// Enable debugging in browser console
eventSource.onerror = (error) => {
  console.error("SSE Error:", error);
};
```

**3. NestJS proxy issues**

```bash
# Check NestJS logs for FastAPI connection
npm run start:dev
# Look for: "FastAPI connection successful"
```

**4. Memory leaks with streaming**

```javascript
// Ensure proper cleanup
useEffect(() => {
  return () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };
}, []);
```

#### Performance Optimization

**1. Adjust streaming delay:**

```python
# In main_streaming.py, modify delay
await asyncio.sleep(0.1)  # Faster: 0.05, Slower: 0.2
```

**2. Enable response compression:**

```python
# Add to FastAPI
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**3. Implement connection pooling:**

```typescript
// In NestJS service
@Injectable()
export class ChatService {
  private httpService = new HttpService({
    timeout: 30000,
    maxRedirects: 5,
  });
}
```

### Deployment Considerations

#### Production Setup

**1. Load Balancer Configuration:**

```nginx
# Nginx config for SSE
location /api/chat/stream {
    proxy_pass http://nestjs-backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_buffering off;
}
```

**2. Environment Variables:**

```bash
# Production settings
STREAMING_ENABLED=true
STREAMING_DELAY=0.05
MAX_CONCURRENT_STREAMS=100
SSE_KEEPALIVE_INTERVAL=30
```

**3. Monitoring and Alerts:**

```yaml
# Docker Compose monitoring
version: "3.8"
services:
  fastapi-streaming:
    image: your-fastapi-streaming:latest
    environment:
      - ENABLE_METRICS=true
      - PROMETHEUS_PORT=9090

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
```

## Deployment and Running

### 1. Start All Services

#### Option A: Regular Chat Mode Only

```bash
# Terminal 1: Start FastAPI (AI Agent)
cd /path/to/aqlon
python main.py
# Runs on http://localhost:8000

# Terminal 2: Start NestJS (Backend API)
cd ai-chat-backend
npm run start:dev
# Runs on http://localhost:3001

# Terminal 3: Start Next.js (Frontend)
cd your-nextjs-app
npm run dev
# Runs on http://localhost:3000
```

#### Option B: Full Stack with Streaming Support

```bash
# Terminal 1: Start FastAPI Streaming Server
cd /path/to/aqlon
python main_streaming.py
# Runs on http://localhost:8000 with streaming support

# Terminal 2: Start NestJS (Backend API with streaming)
cd ai-chat-backend
npm run start:dev
# Runs on http://localhost:3001

# Terminal 3: Start Next.js (Frontend with streaming toggle)
cd your-nextjs-app
npm run dev
# Runs on http://localhost:3000
```

#### Production Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Or using PM2 for process management
pm2 start ecosystem.config.js
```

### 2. Testing the Stack

#### Basic API Testing

```bash
# Test NestJS health (should show FastAPI connection)
curl http://localhost:3001/api/health

# Test session creation through NestJS
curl -X POST http://localhost:3001/api/sessions

# Test regular chat through NestJS
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "your-session-id"}'
```

#### Streaming API Testing

```bash
# Test FastAPI streaming directly
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about business analytics", "session_id": "test-123"}' \
  --no-buffer

# Test streaming through NestJS proxy
curl -X POST http://localhost:3001/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What are key business metrics?"}' \
  --no-buffer

# Test with session continuity
curl -X POST http://localhost:3001/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Follow up question", "session_id": "test-123"}' \
  --no-buffer
```

#### Frontend Testing

1. **Regular Mode Testing:**

   - Open http://localhost:3000
   - Ensure "Enable Streaming" is OFF
   - Send messages and verify instant full responses

2. **Streaming Mode Testing:**

   - Toggle "Enable Streaming" to ON
   - Send messages and verify word-by-word streaming
   - Check typing indicators and visual feedback

3. **Error Handling Testing:**
   - Stop FastAPI server during streaming
   - Verify graceful error handling
   - Test recovery after restarting services

## Benefits of This Architecture

### 🔒 Security & Authentication

- Implement JWT authentication in NestJS
- API key validation
- Rate limiting and DDoS protection
- Input sanitization and validation

### 📊 Monitoring & Logging

- Centralized request logging
- Performance metrics
- Error tracking
- Business analytics

### 🚀 Performance

- Response caching
- Request optimization
- Connection pooling
- Load balancing ready

### 🛠️ Flexibility

- Easy to add new endpoints
- Business logic separation
- Version management
- A/B testing capabilities

This architecture provides a robust, scalable solution for your AI chat application with proper separation of concerns and enterprise-grade features.

## 🚀 Quick Start Guide

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git

### Installation

1. **Clone and setup the AI agent:**

```bash
git clone <your-repo>
cd aqlon
pip install -r requirements.txt
```

2. **Create and setup NestJS backend:**

```bash
npm i -g @nestjs/cli
nest new ai-chat-backend
cd ai-chat-backend
npm install @nestjs/config @nestjs/throttler axios class-validator class-transformer
```

3. **Create Next.js frontend:**

```bash
npx create-next-app@latest your-nextjs-app --typescript --tailwind --app
cd your-nextjs-app
npm install
```

4. **Copy configuration files:**
   - Copy all NestJS implementation files from this README
   - Copy Next.js API client and components
   - Set up environment variables (.env files)

### Running the Complete Stack

```bash
# Terminal 1: FastAPI (with streaming)
cd aqlon
python main_streaming.py

# Terminal 2: NestJS Backend
cd ai-chat-backend
npm run start:dev

# Terminal 3: Next.js Frontend
cd your-nextjs-app
npm run dev
```

### Testing

```bash
# Run comprehensive tests
chmod +x test_streaming.sh
./test_streaming.sh

# Or test manually
curl http://localhost:3001/api/health
curl -X POST http://localhost:3001/api/sessions
```

### Production Deployment

```bash
# Docker deployment
docker-compose up -d

# Or PM2 process management
pm2 start ecosystem.config.js
```

**🎉 Access your application:**

- Frontend: http://localhost:3000
- NestJS API: http://localhost:3001
- FastAPI: http://localhost:8000

---

## 📚 Additional Resources

- **Architecture Documentation**: See above sections for detailed implementation
- **API Reference**: Check `/api/health`, `/api/chat`, `/api/chat/stream` endpoints
- **Troubleshooting**: Review common issues and solutions in the guide
- **Monitoring**: Use Prometheus + Grafana for production monitoring
- **Security**: Implement JWT, rate limiting, and input validation

For support and updates, check the project repository.

---

## 📋 Quick Reference

### **Essential Commands**

```bash
# Complete setup
./deploy.sh setup

# Start development
./deploy.sh dev

# Check health
./health_check.sh

# Run tests
./test_streaming.sh

# Production deployment
docker-compose up -d
```

### **Key Files**

- `main_streaming.py` - FastAPI streaming server
- `README_NESTJS_NEXTJS.md` - Complete implementation guide
- `docker-compose.yml` - Production deployment
- `deploy.sh` - Automated deployment script
- `test_streaming.sh` - Comprehensive test suite

### **Service URLs**

- Frontend: http://localhost:3000
- NestJS API: http://localhost:3001
- FastAPI: http://localhost:8000
- Grafana: http://localhost:3001 (when enabled)

### **Architecture Benefits**

- 🔄 **Dual Mode**: Regular + Streaming chat
- 🛡️ **Security**: Rate limiting, CORS, validation
- 📊 **Monitoring**: Prometheus + Grafana
- 🚀 **Scalable**: Load balancing, clustering
- 🔧 **DevOps**: Automated deployment, health checks

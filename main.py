"""
FastAPI wrapper for the LangGraph chat agent with streaming support
Provides REST API endpoints for Next.js frontend integration
"""

import uuid
import json
import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import logging

from agent.langgraph_workflow import handle_chat, get_chat_history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Business Advisor API with Streaming",
    description="REST API for the AI Business Advisor chat agent with streaming support",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default dev server
        "http://localhost:3001",  # Alternative Next.js port
        "https://localhost:3000",
        "https://localhost:3001",
        # Add your production domains here
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class SessionRequest(BaseModel):
    session_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str

class HistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, str]]

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Business Advisor API with Streaming"}

# Create new chat session
@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest = None):
    """Create a new chat session or return existing session ID"""
    try:
        if request and request.session_id:
            session_id = request.session_id
        else:
            session_id = str(uuid.uuid4())
        
        logger.info(f"Created/Retrieved session: {session_id}")
        return SessionResponse(session_id=session_id)
    
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

# Send chat message (regular, non-streaming)
@app.post("/api/chat", response_model=ChatResponse)
async def send_message(chat_request: ChatMessage):
    """Send a message to the AI agent and get response"""
    try:
        # Generate session ID if not provided
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        if not chat_request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"Processing message for session {session_id}: {chat_request.message[:100]}...")
        
        # Call the chat handler
        response = handle_chat(chat_request.message, session_id)
        
        # Handle response structure
        if isinstance(response, dict):
            if response.get("error"):
                return ChatResponse(
                    response="",
                    session_id=session_id,
                    error=response["error"]
                )
            else:
                return ChatResponse(
                    response=response.get("response", "No response generated"),
                    session_id=session_id,
                    error=None,
                    tokens_used=response.get("tokens_used")
                )
        else:
            return ChatResponse(
                response=str(response),
                session_id=session_id,
                error=None
            )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

# Streaming chat endpoint
@app.post("/api/chat/stream")
async def stream_chat(chat_request: ChatMessage):
    """Stream response from the AI agent word by word"""
    async def event_stream():
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        if not chat_request.message.strip():
            yield f"data: {json.dumps({'error': 'Message cannot be empty', 'session_id': session_id, 'type': 'error'})}\n\n"
            return
        
        try:
            logger.info(f"Streaming message for session {session_id}: {chat_request.message[:100]}...")
            
            # First send session_id
            yield f"data: {json.dumps({'session_id': session_id, 'type': 'session'})}\n\n"
            
            # Get the response from the chat handler
            response = handle_chat(chat_request.message, session_id)
            
            if isinstance(response, dict):
                if response.get("error"):
                    yield f"data: {json.dumps({'error': response['error'], 'session_id': session_id, 'type': 'error'})}\n\n"
                    return
                
                response_text = response.get("response", "No response generated")
            else:
                response_text = str(response)
            
            # Stream the response word by word
            words = response_text.split()
            for i, word in enumerate(words):
                chunk_data = {
                    'content': word,
                    'type': 'content',
                    'session_id': session_id,
                    'index': i
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                # Add small delay to simulate streaming
                await asyncio.sleep(0.1)
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'session_id': session_id, 'type': 'error'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Get chat history
@app.get("/api/sessions/{session_id}/history", response_model=HistoryResponse)
async def get_session_history(session_id: str):
    """Get chat history for a specific session"""
    try:
        logger.info(f"Retrieving history for session: {session_id}")
        
        history = get_chat_history(session_id)
        
        return HistoryResponse(
            session_id=session_id,
            history=history
        )
    
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

# Clear session (optional - creates new session)
@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session (note: creates a new session ID)"""
    try:
        new_session_id = str(uuid.uuid4())
        logger.info(f"Cleared session {session_id}, new session: {new_session_id}")
        
        return SessionResponse(session_id=new_session_id)
    
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

# List active sessions (basic endpoint)
@app.get("/api/sessions")
async def list_sessions():
    """List sessions - basic implementation"""
    return {"message": "Session listing not implemented yet - sessions are managed per request"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Business Advisor API with Streaming",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "create_session": "POST /api/sessions",
            "send_message": "POST /api/chat",
            "stream_message": "POST /api/chat/stream",
            "get_history": "GET /api/sessions/{session_id}/history",
            "clear_session": "DELETE /api/sessions/{session_id}"
        }
    }

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

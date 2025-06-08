# filepath: /Users/al-husseinabdullah/aqlon/agent/chat_handler.py
import os
import uuid
from langgraph.checkpoint.postgres import PostgresSaver

def create_session_id() -> str:
    """Create a proper UUID session ID."""
    return str(uuid.uuid4())

def get_postgres_checkpointer():
    """Create and return a PostgreSQL checkpointer context manager for LangGraph."""
    connection_string = os.getenv("DATABASE_URL")
    if not connection_string:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return PostgresSaver.from_conn_string(connection_string)

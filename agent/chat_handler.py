import os
import logging
import uuid
from typing import Dict, List, Any, Tuple
from datetime import datetime
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain.schema import HumanMessage, BaseMessage
from langchain_community.callbacks.manager import get_openai_callback
from langchain.agents import AgentExecutor

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS_PER_DAY = 100000  # Adjust based on your needs
MAX_MESSAGES_PER_MINUTE = 10
MAX_HISTORY_LENGTH = 50  # Maximum number of messages to keep in history


class ChatHandler:
    def __init__(self, agent, tools):
        """Initialize the chat handler with agent and tools."""
        self.agent = agent
        self.tools = tools
        
        # Initialize rate limiting
        self.message_timestamps: List[datetime] = []
        self.daily_token_count = 0
        self.last_reset = datetime.now()

    def _check_rate_limits(self) -> Tuple[bool, str]:
        """Check if the current request exceeds rate limits."""
        now = datetime.now()
        
        # Reset daily token count if it's a new day
        if (now - self.last_reset).days >= 1:
            self.daily_token_count = 0
            self.last_reset = now
        
        # Check messages per minute
        self.message_timestamps = [ts for ts in self.message_timestamps 
                                 if (now - ts).total_seconds() < 60]
        if len(self.message_timestamps) >= MAX_MESSAGES_PER_MINUTE:
            return False, "Rate limit exceeded: Too many messages per minute"
        
        # Check daily token limit
        if self.daily_token_count >= MAX_TOKENS_PER_DAY:
            return False, "Rate limit exceeded: Daily token limit reached"
        
        return True, ""

    def _get_memory(self, session_id: str) -> PostgresChatMessageHistory:
        """Get or create a persistent chat memory for the session."""
        return PostgresChatMessageHistory(
            connection_string=os.getenv("DATABASE_URL"),
            session_id=session_id,
            table_name="chat_history"
        )

    def _truncate_history(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Truncate history to maintain maximum length."""
        if len(messages) > MAX_HISTORY_LENGTH:
            return messages[-MAX_HISTORY_LENGTH:]
        return messages

    def handle_chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Handle a chat message and return a response with metadata.
        
        Args:
            message: The user's message
            session_id: Unique identifier for the chat session
            
        Returns:
            Dict containing:
            - response: The AI's response
            - tokens_used: Number of tokens used
            - error: Any error message
            - history: Current chat history
        """
        try:
            # Check rate limits
            can_proceed, error_msg = self._check_rate_limits()
            if not can_proceed:
                return {
                    "response": None,
                    "tokens_used": 0,
                    "error": error_msg,
                    "history": []
                }
            
            # Get or create memory for this session
            memory = self._get_memory(session_id)
            messages = memory.messages
            
            # Create agent executor with memory
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True
            )
            
            # Track token usage
            with get_openai_callback() as cb:
                # Process the message
                response = agent_executor.invoke({
                    "input": message,
                    "chat_history": self._truncate_history(messages)
                })
                
                # Update token count
                self.daily_token_count += cb.total_tokens
                self.message_timestamps.append(datetime.now())
            
            # Save the interaction
            memory.add_user_message(message)
            memory.add_ai_message(response["output"])
            
            return {
                "response": response["output"],
                "tokens_used": cb.total_tokens,
                "error": None,
                "history": self._truncate_history(memory.messages)
            }
            
        except Exception as e:
            logger.error(f"Error in handle_chat: {str(e)}", exc_info=True)
            return {
                "response": None,
                "tokens_used": 0,
                "error": f"Error processing message: {str(e)}",
                "history": []
            }

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get the chat history for a session."""
        try:
            memory = self._get_memory(session_id)
            return [
                {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                    "timestamp": msg.additional_kwargs.get("timestamp", "")
                }
                for msg in self._truncate_history(memory.messages)
            ]
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}", exc_info=True)
            return []


def handle_chat(message: str, session_id: str, chat_handler: ChatHandler) -> Dict[str, Any]:
    """Wrapper function to handle chat messages."""
    return chat_handler.handle_chat(message, session_id)


def get_chat_history(session_id: str, chat_handler: ChatHandler) -> List[Dict[str, str]]:
    """Wrapper function to get chat history."""
    return chat_handler.get_chat_history(session_id)


def create_session_id() -> str:
    """Create a proper UUID session ID."""
    return str(uuid.uuid4())








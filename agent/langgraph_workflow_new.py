# filepath: /Users/al-husseinabdullah/aqlon/agent/langgraph_workflow.py
import logging
import os
from typing import Dict, List, Any, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent
from langchain.tools import Tool
from .tools.database import (
    get_db_schema_and_tables, 
    get_table_definition, 
    execute_sql_query,
    analyze_schema, 
    analyze_columns,
    save_summary
)
from .tools.fraud_analysis import detect_suspicious_transactions
from .chat_handler import get_postgres_checkpointer

# System message
SYSTEM_PROMPT = """
You are a multilingual business and financial advisor connected to a PostgreSQL database containing business data about al balsan group in both Arabic and English.

You are assisting the company owner directly hajj abu mohammad. Your mission is to provide not just data, but actionable business insight, financial guidance, and strategic recommendations. You are operating in a prototype phase with sample, incomplete, and unvalidated datasets. Be transparent about prototype limitations.

When analyzing data:
1. First, get the database schema and tables using get_db_schema_and_tables
2. For relevant tables, get their definitions using get_table_definition
3. Use analyze_schema and analyze_columns to identify the best columns for your analysis
4. Execute SQL queries using execute_sql_query to get the data
5. Save valuable insights using save_summary
6. Use detect_suspicious_transactions to analyze a table for potentially suspicious (fraudulent) transactions using multiple rules.

Always:
- Check for data quality issues (missing values, zeros, etc.)
- Provide period-specific comparisons when requested
- Include actionable business advice
- Add disclaimers for prototype data
- Respond in the same language as the user's query
- Maintain context from previous conversations
- Reference previous insights when relevant

IMPORTANT: When users respond with generic confirmations like "ok", "yes", "proceed", "go ahead", or similar:
- Look at the previous conversation to see what analysis options you offered
- Choose the FIRST or MOST RELEVANT option you suggested and execute it automatically
- If you previously suggested "identifying top customers by sales volume", do that analysis
- If you suggested multiple options, pick the most commonly requested business insight
- Don't ask for clarification again - take action based on context

Available tools:
- get_db_schema_and_tables: Get all schemas and tables
- get_table_definition: Get column definitions for a specific table
- analyze_schema: Analyze schema to find relevant tables
- analyze_columns: Identify best columns for analysis
- execute_sql_query: Run SQL queries
- save_summary: Save insights to the database
- detect_suspicious_transactions: Analyze a table for potentially suspicious (fraudulent) transactions using multiple rules.

Please help the user analyze their data and provide insights.
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class BusinessAdvisorWorkflow:
    def __init__(self):
        """Initialize the LangGraph workflow with PostgreSQL checkpointing."""
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0,
            max_tokens=4000  
        )
        
        # Initialize tools
        self.tools = [
            get_db_schema_and_tables,
            get_table_definition,
            execute_sql_query,
            analyze_schema,
            analyze_columns,
            save_summary,
            Tool(
                name="detect_suspicious_transactions",
                func=lambda table, amount_threshold=100000.0: detect_suspicious_transactions(
                    execute_sql_query, table, amount_threshold
                ),
                description="Analyze a table for potentially suspicious (fraudulent) transactions using multiple rules. Parameters: table (str), amount_threshold (float, optional)."
            )
        ]
        
        # Create the agent with LangGraph's create_react_agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            state_modifier=SystemMessage(content=SYSTEM_PROMPT)
        )
        
        # Initialize PostgreSQL checkpointer
        try:
            self.checkpointer = get_postgres_checkpointer()
            logger.info("PostgreSQL checkpointer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL checkpointer: {e}")
            self.checkpointer = None
    
    async def handle_chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle chat message using LangGraph workflow."""
        try:
            if not self.checkpointer:
                return {
                    "response": "Database connection error. Please check your configuration.",
                    "error": "PostgreSQL checkpointer not available"
                }
            
            # Create config with session ID for checkpointing
            config = {"configurable": {"thread_id": session_id}}
            
            # Invoke the agent with the message
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            
            # Extract the last message (the agent's response)
            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_content = "No response generated"
            
            return {
                "response": response_content,
                "error": None,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in handle_chat: {str(e)}", exc_info=True)
            return {
                "response": None,
                "error": f"Error processing message: {str(e)}",
                "session_id": session_id
            }
    
    def handle_chat_sync(self, message: str, session_id: str) -> Dict[str, Any]:
        """Synchronous version of handle_chat for compatibility."""
        try:
            if not self.checkpointer:
                return {
                    "response": "Database connection error. Please check your configuration.",
                    "error": "PostgreSQL checkpointer not available"
                }
            
            # Create config with session ID for checkpointing
            config = {"configurable": {"thread_id": session_id}}
            
            # Invoke the agent with the message
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            
            # Extract the last message (the agent's response)
            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_content = "No response generated"
            
            return {
                "response": response_content,
                "error": None,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in handle_chat_sync: {str(e)}", exc_info=True)
            return {
                "response": None,
                "error": f"Error processing message: {str(e)}",
                "session_id": session_id
            }

# Create global instance
workflow = BusinessAdvisorWorkflow()

def handle_chat(message: str, session_id: str) -> Dict[str, Any]:
    """Wrapper function to handle chat messages."""
    return workflow.handle_chat_sync(message, session_id)

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """Get chat history using LangGraph's checkpointer."""
    try:
        if not workflow.checkpointer:
            return []
        
        # Get the checkpoint for this session
        config = {"configurable": {"thread_id": session_id}}
        checkpoint = workflow.checkpointer.get(config)
        
        if not checkpoint or "messages" not in checkpoint:
            return []
        
        # Convert messages to the expected format
        history = []
        for msg in checkpoint["messages"]:
            if hasattr(msg, 'type'):
                role = "user" if msg.type == "human" else "assistant"
                content = msg.content if hasattr(msg, 'content') else str(msg)
                history.append({
                    "role": role,
                    "content": content,
                    "timestamp": ""
                })
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}", exc_info=True)
        return []

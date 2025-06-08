import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import create_openai_functions_agent
from .tools.database import (
    get_db_schema_and_tables, 
    get_table_definition, 
    execute_sql_query,
    analyze_schema, 
    analyze_columns,
    save_summary
)
from .chat_handler import ChatHandler

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

class ChatManager:
    def __init__(self):
        """Initialize the chat manager with all necessary components."""
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=4000  # Adjust based on your needs
        )
        
        # Initialize tools
        self.tools = [
            get_db_schema_and_tables,
            get_table_definition,
            execute_sql_query,
            analyze_schema,
            analyze_columns,
            save_summary
        ]
        
        # Create the prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}"),
        ])
        
        # Create the agent
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        
        # Initialize the chat handler
        self.chat_handler = ChatHandler(self.agent, self.tools)

    def handle_chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle chat message using the chat handler."""
        return self.chat_handler.handle_chat(message, session_id)

    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get chat history using the chat handler."""
        return self.chat_handler.get_chat_history(session_id)

# Initialize the chat manager
chat_manager = ChatManager()

def handle_chat(message: str, session_id: str) -> Dict[str, Any]:
    """Wrapper function to handle chat messages."""
    return chat_manager.handle_chat(message, session_id)

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """Wrapper function to get chat history."""
    return chat_manager.get_chat_history(session_id) 
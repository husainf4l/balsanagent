import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from langchain_openai import ChatOpenAI
from langchain_postgres import PostgresChatMessageHistory
import uuid
from langchain_core.messages import HumanMessage
import traceback

# Load environment variables
load_dotenv()

def test_database_connection():
    print("\nTesting Database Connection...")
    try:
        conn = psycopg.connect(
            dbname=os.getenv("POSTGRES_DB", "balsanaiagent"),
            user=os.getenv("POSTGRES_USER", "husain"),
            password=os.getenv("POSTGRES_PASSWORD", "tt55oo77"),
            host=os.getenv("POSTGRES_HOST", "149.200.251.12"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            row_factory=dict_row
        )
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version();")
            result = cur.fetchone()
            print("✅ Database connection successful!")
            print(f"Connected to: {result['current_database']}")
            print(f"User: {result['current_user']}")
            print(f"Version: {result['version']}")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return None

def test_openai():
    print("\nTesting OpenAI Connection...")
    try:
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        response = llm.invoke("Say hello!")
        print("✅ OpenAI connection successful!")
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {str(e)}")
        return False

def test_chat_history(conn):
    print("\nTesting Chat History...")
    try:
        # Create a new connection specifically for chat history
        chat_conn = psycopg.connect(
            dbname=os.getenv("POSTGRES_DB", "balsanaiagent"),
            user=os.getenv("POSTGRES_USER", "husain"),
            password=os.getenv("POSTGRES_PASSWORD", "tt55oo77"),
            host=os.getenv("POSTGRES_HOST", "149.200.251.12"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        print(f"Chat connection object: {chat_conn}")
        table_name = "chat_history"
        session_id = str(uuid.uuid4())
        # Ensure table exists
        PostgresChatMessageHistory.create_tables(chat_conn, table_name)
        chat_history = PostgresChatMessageHistory(
            table_name,
            session_id,
            sync_connection=chat_conn
        )
        chat_history.add_messages([HumanMessage(content="Test message")])
        messages = chat_history.messages
        print("✅ Chat history test successful!")
        print(f"Messages: {messages}")
        return True
    except Exception as e:
        print(f"❌ Chat history test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    print("Starting component tests...")
    
    # Test database connection
    conn = test_database_connection()
    if not conn:
        print("❌ Database test failed, stopping further tests")
        return
    
    # Test OpenAI
    if not test_openai():
        print("❌ OpenAI test failed, stopping further tests")
        return
    
    # Test chat history
    if not test_chat_history(conn):
        print("❌ Chat history test failed")
        return
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    main() 
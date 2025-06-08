import os
import sys
import uuid

# Add the parent directory to the Python path so we can import the agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.langgraph_workflow import handle_chat

def main():
    # Generate a unique session ID for this test
    session_id = str(uuid.uuid4())
    print(f"Starting new chat session: {session_id}")
    print("=" * 50)
    print("Interactive Chat with Database Agent")
    print("Type 'quit', 'exit', or 'bye' to end the session")
    print("Type 'clear' to start a new session")
    print("=" * 50)

    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Chat session ended.")
                break
            
            # Check for empty input
            if not user_input:
                print("Please enter a question or command.")
                continue
            
            # Handle clear command
            if user_input.lower() == 'clear':
                session_id = str(uuid.uuid4())
                print(f"\nNew chat session started: {session_id}")
                continue
            
            # Process the query
            print("\nAgent is thinking...")
            response = handle_chat(user_input, session_id)
            
            # Handle the response structure
            if isinstance(response, dict):
                if response.get("error"):
                    print(f"\nError: {response['error']}")
                else:
                    print(f"\nAssistant: {response.get('response', 'No response')}")
                    if response.get('tokens_used'):
                        print(f"Tokens used: {response['tokens_used']}")
            else:
                print(f"\nAssistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main() 


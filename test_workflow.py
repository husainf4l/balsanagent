from langgraph_workflow import handle_chat

# Test the workflow with a sample query
test_query = "compare the the total sales 2024 and 2025"
print("Sending query:", test_query)
response = handle_chat(test_query)
print("\nResponse:", response) 
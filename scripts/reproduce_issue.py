
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from summarizer.langchain_chat import LangChainChat
from langchain_core.messages import AIMessage, HumanMessage

def mock_llm_invoke(*args, **kwargs):
    return AIMessage(content="Mock response")

class MockChatOllama:
    def __init__(self, *args, **kwargs):
        pass
    def __or__(self, other):
        return self
    def invoke(self, *args, **kwargs):
        return AIMessage(content="Mock response")
    def stream(self, *args, **kwargs):
        yield AIMessage(content="Mock response")

# Patch ChatOllama to avoid real LLM calls
import langchain_ollama
langchain_ollama.ChatOllama = MockChatOllama

def reproduce():
    print("Initializing Chat...")
    chat = LangChainChat()
    
    # inject a message with curly braces into history
    print("Injecting message with braces...")
    chat.chat_history.add_user_message("Show me some json")
    chat.chat_history.add_ai_message('Here is a json: {"key": "value", "ai_suggestion": "test"}')
    
    print("Asking next question...")
    response = chat.chat("Next question", stream=False)
    
    print(f"Response: {response}")
    
    if "Error" in response and "missing variables" in response:
        print("SUCCESS: Reproduced the error.")
    else:
        print("FAILED: Could not reproduce the error.")

if __name__ == "__main__":
    reproduce()

#!/usr/bin/env python3
"""
Example of multi-shot conversation with GrokClient.
This demonstrates how to maintain a conversation context on the client side.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from grok.client import GrokClient, Message

async def main():
    # Initialize client
    client = GrokClient()

    # Start a conversation about Python programming
    messages = [
        Message(role="user", content="What is Python?")
    ]
    
    # Get first response (start new chat)
    response = await client.chat_completion_async(messages, new_chat=True, log_level="DEBUG")
    print("\nQuestion: What is Python?")
    print("Response:", response.content)

    # Add the response to our conversation and ask a follow-up
    messages.extend([
        Message(role="assistant", content=response.content),
        Message(role="user", content="What makes it different from other programming languages?")
    ])
    
    # Get second response (continue in same chat)
    response = await client.chat_completion_async(messages, new_chat=False, log_level="DEBUG")
    print("\nQuestion: What makes it different from other programming languages?")
    print("Response:", response.content)

    # Continue the conversation about Python features
    messages.extend([
        Message(role="assistant", content=response.content),
        Message(role="user", content="Can you give me an example of Python's simplicity?")
    ])
    
    # Get third response (continue in same chat)
    response = await client.chat_completion_async(messages, new_chat=False, log_level="DEBUG")
    print("\nQuestion: Can you give me an example of Python's simplicity?")
    print("Response:", response.content)

    # Ask about practical applications
    messages.extend([
        Message(role="assistant", content=response.content),
        Message(role="user", content="What are some real-world applications built with Python?")
    ])
    
    # Get final response (continue in same chat)
    response = await client.chat_completion_async(messages, new_chat=False, log_level="DEBUG")
    print("\nQuestion: What are some real-world applications built with Python?")
    print("Response:", response.content)

    # Print the entire conversation history
    print("\nFull conversation history:")
    for msg in messages:
        print(f"\n{msg.role.upper()}: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main()) 
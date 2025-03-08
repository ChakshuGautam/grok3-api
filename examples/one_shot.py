#!/usr/bin/env python3
"""
Example of one-shot usage of GrokClient.
Each request is independent and starts a new chat.
"""

import os
import sys
# Add the project root to the Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from grok.client import GrokClient, Message

async def main():
    # Initialize client with debug logging
    client = GrokClient(log_level="DEBUG")  # Set default log level here
    
    print("Running with default log level (ERROR)...")
    
    # Example 1: Generate a haiku
    response = await client.chat_completion_async([
        Message(role="user", content="Write a haiku about coding")
    ])
    print("\nHaiku about coding:")
    print(response.content)

    # # Example with different log level for a specific request
    # print("\nRunning with DEBUG log level for this request only...")
    # response = await client.chat_completion_async(
    #     [Message(role="user", content="What is Python used for?")],
    #     log_level="DEBUG"  # Override log level for this request only
    # )
    # print("\nPython use cases:")
    # print(response.content)

    # # Example 2: Explain a concept
    # response = await client.chat_completion_async([
    #     Message(role="user", content="Explain quantum computing in one paragraph")
    # ])
    # print("\nQuantum computing explanation:")
    # print(response.content)

    # # Example 3: Solve a problem
    # response = await client.chat_completion_async([
    #     Message(role="user", content="What's the fastest way to sort a million integers in Python?")
    # ])
    # print("\nSorting solution:")
    # print(response.content)

if __name__ == "__main__":
    asyncio.run(main()) 
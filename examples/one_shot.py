#!/usr/bin/env python3
"""
Example of one-shot usage of GrokClient.
Each request is independent and starts a new chat.
"""

import asyncio
from grok_client import GrokClient, Message

async def main():
    # Initialize client
    client = GrokClient()

    # Example 1: Generate a haiku
    response = await client.chat_completion_async([
        Message(role="user", content="Write a haiku about coding")
    ])
    print("\nHaiku about coding:")
    print(response.content)

    # Example 2: Explain a concept
    response = await client.chat_completion_async([
        Message(role="user", content="Explain quantum computing in one paragraph")
    ])
    print("\nQuantum computing explanation:")
    print(response.content)

    # Example 3: Solve a problem
    response = await client.chat_completion_async([
        Message(role="user", content="What's the fastest way to sort a million integers in Python?")
    ])
    print("\nSorting solution:")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main()) 
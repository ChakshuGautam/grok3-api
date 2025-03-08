#!/usr/bin/env python3
"""
Example of streaming responses with GrokClient.
Demonstrates real-time token streaming and non-streaming modes.
"""

import os
import sys
# Add the project root to the Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from grok.client import GrokClient, Message

async def test_streaming_mode():
    """Test response with streaming enabled, printing tokens as they arrive."""
    print("\n*** Testing Streaming Mode ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Sending long message with streaming enabled...")
    print("\nReceiving response in real-time:")
    print("-" * 50)
    
    accumulated_text = ""
    async for chunk in client.chat_completion_async(
        [
            Message(
                role="user",
                content="Write a detailed essay about the history and future of artificial intelligence"
            )
        ],
        stream=True  # Enable streaming
    ):
        # Print each new token as it arrives
        new_text = chunk.content
        print(new_text, end="", flush=True)
        accumulated_text += new_text
    
    print("\n" + "-" * 50)
    print(f"\nFinal response metadata:")
    print(f"Total length: {len(accumulated_text)} characters")
    print(f"Is complete: {chunk.is_complete}")
    print(f"Response ID: {chunk.response_id}")

# async def test_non_streaming_mode():
#     """Test response with streaming disabled (complete response at once)."""
#     print("\n*** Testing Non-Streaming Mode ***")
#     client = GrokClient(log_level="DEBUG")
    
#     print("Sending message without streaming...")
#     response = await client.chat_completion_async(
#         [
#             Message(
#                 role="user",
#                 content="Write a short paragraph about Python programming"
#             )
#         ],
#         stream=False  # Disable streaming (default behavior)
#     )
    
#     print(f"\nResponse received (complete):")
#     print("-" * 50)
#     print(response.content)
#     print("-" * 50)
#     print(f"\nMetadata:")
#     print(f"Length: {len(response.content)} characters")
#     print(f"Is complete: {response.is_complete}")
#     print(f"Response ID: {response.response_id}")

# async def test_long_streaming():
#     """Test how streaming handles very long responses in real-time."""
#     print("\n*** Testing Long Streaming Response ***")
#     client = GrokClient(log_level="DEBUG")
    
#     print("Sending request for a very long response...")
#     print("\nReceiving long response in real-time:")
#     print("-" * 50)
    
#     token_count = 0
#     async for chunk in client.chat_completion_async(
#         [
#             Message(
#                 role="user",
#                 content="Write a comprehensive guide to machine learning, including all major algorithms and their applications"
#             )
#         ],
#         stream=True
#     ):
#         # Print progress indicator for each token
#         print(chunk.content, end="", flush=True)
#         token_count += 1
#         if token_count % 100 == 0:  # Show progress every 100 tokens
#             print(f"\n[Received {token_count} tokens so far...]", end="\r", flush=True)
    
#     print("\n" + "-" * 50)
#     print(f"\nStreaming complete:")
#     print(f"Total tokens received: {token_count}")
#     print(f"Is complete: {chunk.is_complete}")
#     print(f"Response ID: {chunk.response_id}")

async def main():
    """Run streaming examples in sequence."""
    print("Running streaming response examples...")
    
    # Test basic streaming mode with real-time output
    await test_streaming_mode()
    
    # # Test non-streaming mode (complete response)
    # await test_non_streaming_mode()
    
    # # Test with very long streaming response
    # await test_long_streaming()
    
    print("\nAll streaming examples completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Example of deep search with GrokClient.
Demonstrates how deep search enhances responses with web-sourced information.
"""

import os
import sys
# Add the project root to the Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from grok.client import GrokClient, Message

async def test_current_events():
    """Test deep search with current events query."""
    print("\n*** Testing Deep Search: Who is the president of the United States? ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Querying about recent developments...")
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="Who is the president of the United States?",
            deep_search=True
        )
    ])
    
    print(f"\nResponse received:")
    print(f"Is complete: {response.is_complete}")
    print(f"\nContent preview: {response.content[:200]}...")

async def test_technical_research():
    """Test deep search with technical research query."""
    print("\n*** Testing Deep Search: Technical Research ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Researching technical topic...")
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="What are the most promising approaches to fusion energy, and what recent breakthroughs have been made?",
            deep_search=True
        )
    ])
    
    print(f"\nResponse received:")
    print(f"Is complete: {response.is_complete}")
    print(f"\nContent preview: {response.content[:200]}...")

async def test_combined_search():
    """Test deep search combined with think mode."""
    print("\n*** Testing Deep Search with Think Mode ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Analyzing complex topic with both deep search and think mode...")
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="Analyze the environmental impact of different renewable energy sources. Compare their efficiency, cost, and scalability.",
            deep_search=True,
            think_mode=True
        )
    ])
    
    print(f"\nResponse received:")
    print(f"Is thinking: {response.is_thinking}")
    print(f"Is complete: {response.is_complete}")
    print(f"\nContent preview: {response.content[:200]}...")

async def main():
    """Run deep search examples in sequence."""
    print("Running deep search examples...")
    
    # Test current events search
    await test_current_events()
    
    # Test technical research
    await test_technical_research()
    
    # Test combined search with think mode
    await test_combined_search()
    
    print("\nAll deep search examples completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
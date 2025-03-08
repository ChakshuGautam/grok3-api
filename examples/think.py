#!/usr/bin/env python3
"""
Example of think mode with GrokClient.
Demonstrates how think mode helps with complex problem solving.
"""

import os
import sys
# Add the project root to the Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from grok.client import GrokClient, Message

async def test_basic_think():
    """Test basic think mode with a comparison task."""
    print("\n*** Testing Basic Think Mode ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Comparing programming paradigms with think mode...")
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="Compare and contrast the major programming paradigms: OOP, functional, and procedural programming",
            think_mode=True
        )
    ])
    
    print(f"\nResponse received:")
    print(f"Is thinking: {response.is_thinking}")
    print(f"Is complete: {response.is_complete}")
    print(f"\nContent preview: {response.content[:200]}...")

async def test_problem_solving():
    """Test think mode with a complex problem solving task."""
    print("\n*** Testing Problem Solving with Think Mode ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Solving a complex programming problem...")
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="Design a scalable microservices architecture for an e-commerce platform. Consider authentication, product catalog, shopping cart, and order processing.",
            think_mode=True
        )
    ])
    
    print(f"\nResponse received:")
    print(f"Is thinking: {response.is_thinking}")
    print(f"Is complete: {response.is_complete}")
    print(f"\nContent preview: {response.content[:200]}...")

async def test_analysis():
    """Test think mode with an analysis task."""
    print("\n*** Testing Analysis with Think Mode ***")
    client = GrokClient(log_level="DEBUG")
    
    print("Analyzing a complex topic...")
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="Analyze the impact of artificial intelligence on future job markets. Consider both positive and negative effects, and suggest strategies for workforce adaptation.",
            think_mode=True
        )
    ])
    
    print(f"\nResponse received:")
    print(f"Is thinking: {response.is_thinking}")
    print(f"Is complete: {response.is_complete}")
    print(f"\nContent preview: {response.content[:200]}...")

async def main():
    """Run think mode examples in sequence."""
    print("Running think mode examples...")
    
    # Test basic think mode
    await test_basic_think()
    
    # # Test problem solving with think mode
    # await test_problem_solving()
    
    # # Test analysis with think mode
    # await test_analysis()
    
    print("\nAll think mode examples completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
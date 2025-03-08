#!/usr/bin/env python3
"""
Example of using GrokClient with PDF files.
This demonstrates how to analyze the SICP (Structure and Interpretation of Computer Programs) PDF.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from grok.client import GrokClient, Message, FileAttachment
from pathlib import Path

async def main():
    print("\n*** PDF Upload Test with Debug Mode ***")
    
    # Initialize client with debug mode enabled
    client = GrokClient(debug_mode=True)  

    # Get path to SICP PDF
    pdf_path = Path(__file__).parent / "sicp.small.pdf"
    if not pdf_path.exists():
        print(f"Error: Could not find {pdf_path}")
        sys.exit(1)
    
    print(f"\nFile to upload: {pdf_path} (exists: {pdf_path.exists()}, size: {pdf_path.stat().st_size} bytes)")

    # Simple question to analyze the PDF
    print("\nSending PDF upload request...")
    try:
        response = await client.chat_completion_async([
            Message(
                role="user",
                content="What is this PDF about? Give me a brief summary.",
                attachments=[FileAttachment(pdf_path)]
            )
        ])
        print("\nResponse received successfully!")
        print("Summary:", response.content)
    except Exception as e:
        print(f"\nError during request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 
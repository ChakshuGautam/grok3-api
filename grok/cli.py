#!/usr/bin/env python3
"""
Command-line interface for the Grok API client.
This module provides a simple CLI for interacting with Grok.

Usage:
    python -m grok.cli --port 9222 --message "Your message here" [--new-chat] [--think-mode] [--deep-search] [--files file1 file2 ...]
"""

import sys
import argparse
from pathlib import Path
from .chat import chat_with_grok
import asyncio

def main():
    """Main entry point for CLI interface."""
    parser = argparse.ArgumentParser(description="Chat with Grok using an existing Chrome instance")
    parser.add_argument("--port", type=int, default=9222, help="Chrome remote debugging port")
    parser.add_argument("--message", type=str, required=True, help="Message to send to Grok")
    parser.add_argument("--new-chat", action="store_true", help="Start a new chat instead of continuing existing one")
    parser.add_argument("--think-mode", action="store_true", help="Enable Think mode")
    parser.add_argument("--deep-search", action="store_true", help="Enable DeepSearch mode")
    parser.add_argument("--files", nargs="*", type=Path, help="Files to upload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose logging")
    parser.add_argument("--save-api-response", action="store_true", help="Save the raw API responses to a file")
    parser.add_argument("--export-content", action="store_true", help="Export just the response content to a text file")
    args = parser.parse_args()
    
    asyncio.run(chat_with_grok(
        args.port, 
        args.message, 
        args.new_chat, 
        args.think_mode, 
        args.deep_search, 
        args.files,
        args.debug,
        args.save_api_response,
        args.export_content
    ))

if __name__ == "__main__":
    main() 
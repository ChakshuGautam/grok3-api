#!/usr/bin/env python3
"""
Main entry point for running the grok package as a module.
This enables running the package directly with `python -m grok`.

Example:
    python -m grok --message "Your message to Grok" --debug
"""

from .cli import main

if __name__ == "__main__":
    main() 
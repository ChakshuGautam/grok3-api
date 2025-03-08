#!/usr/bin/env python3
"""
Test script for the Grok response parser using real-world examples.
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any
from grok.parser.response_parser import GrokResponseParser, parse_grok_response

# Color codes for terminal output
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'

def test_example_file(file_path: Path) -> Dict[str, Any]:
    """Test parsing an example file."""
    print(f"{BLUE}Testing file: {BOLD}{file_path.name}{ENDC}")
    
    # Create a parser
    parser = GrokResponseParser()
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse the content
    try:
        result = parser.parse_response(content)
        
        # Print results
        if result['success']:
            print(f"{GREEN}✓ Successfully parsed file{ENDC}")
            print(f"  Format: {result['format']}")
            
            if result['format'] == 'streaming':
                print(f"  Total chunks: {result.get('chunks_count', 0)}")
                print(f"  Valid chunks: {result.get('valid_chunks_count', 0)}")
                print(f"  Tokens extracted: {len(result.get('tokens', []))} tokens")
                
                # Print the first 100 chars of the text
                text = result.get('text', '')
                print(f"  Text (first 100 chars): {text[:100]}...")
                
                # Check if response is marked as complete
                is_complete = result.get('is_complete', False)
                if is_complete:
                    print(f"  {GREEN}Response marked as complete{ENDC}")
                else:
                    print(f"  {YELLOW}Response not marked as complete{ENDC}")
            else:
                # For standard format, print some basic info
                if 'data' in result and isinstance(result['data'], dict):
                    if 'response' in result['data']:
                        response = result['data']['response']
                        print(f"  Response ID: {response.get('responseId', 'N/A')}")
                        if 'message' in response and 'content' in response['message']:
                            content = response['message']['content']
                            print(f"  Content (first 100 chars): {content[:100]}...")
        else:
            print(f"{RED}✗ Failed to parse file: {result.get('message', 'Unknown error')}{ENDC}")
        
        return result
    
    except Exception as e:
        print(f"{RED}✗ Exception during parsing: {str(e)}{ENDC}")
        return {'success': False, 'message': str(e), 'exception': True}

def main():
    """Main function to test all example files."""
    # Check if a directory is provided
    if len(sys.argv) > 1:
        examples_dir = Path(sys.argv[1])
    else:
        # Default to the examples/data directory within the package
        script_dir = Path(__file__).parent
        examples_dir = script_dir / "data"
    
    if not examples_dir.exists() or not examples_dir.is_dir():
        print(f"{RED}Error: {examples_dir} is not a valid directory{ENDC}")
        return
    
    print(f"{BLUE}{BOLD}Testing Grok API response parser with examples from {examples_dir}{ENDC}")
    print()
    
    # Get all .txt files in the directory
    example_files = sorted(examples_dir.glob("*.txt"))
    
    if not example_files:
        print(f"{YELLOW}No example files found in {examples_dir}{ENDC}")
        return
    
    # Test each file
    results = {}
    for i, file_path in enumerate(example_files):
        print(f"{BOLD}Example {i+1}/{len(example_files)}{ENDC}")
        results[file_path.name] = test_example_file(file_path)
        print()
    
    # Print summary
    print(f"{BLUE}{BOLD}Summary:{ENDC}")
    success_count = sum(1 for r in results.values() if r['success'])
    print(f"Processed {len(results)} files: {GREEN}{success_count} succeeded{ENDC}, {RED}{len(results) - success_count} failed{ENDC}")
    
    # If there are any failures, list them
    if success_count < len(results):
        print(f"\n{RED}Failed files:{ENDC}")
        for name, result in results.items():
            if not result['success']:
                print(f"  - {name}: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main() 
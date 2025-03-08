# Grok API Client

A Python package for interacting with the Grok API and parsing its responses.

## Overview

This package provides a client for interacting with Grok via a Chrome browser instance, as well as utilities for parsing and processing Grok API responses.

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/yourusername/grok3-api.git
cd grok3-api
pip install -r requirements.txt
```

## Package Structure

```
grok/               # Main package
├── __init__.py     # Package initialization
├── __main__.py     # Entry point for running as module
├── chat.py         # Main Grok chat client
├── cli.py          # Command-line interface
├── client.py       # Higher-level client with OpenAI-like interface
├── parser/         # Parser subpackage
│   ├── __init__.py
│   ├── response_parser.py    # Grok API response parser
│   └── test_response_parser.py   # Unit tests for the parser
└── examples/       # Examples subpackage
    ├── __init__.py
    ├── data/       # Example data files
    └── test_parser.py  # Script to test parser with examples
examples/           # Example scripts showing usage
├── one_shot.py     # One-shot usage examples
├── multi_shot.py   # Multi-turn conversation examples
└── pdf_analysis.py # PDF analysis examples
```

## Usage

### Using the CLI

You can use the package as a command-line tool:

```bash
python -m grok --port 9222 --message "Your message to Grok"
```

Common options:
- `--port`: Chrome remote debugging port (default: 9222)
- `--message`: Message to send to Grok (required)
- `--new-chat`: Start a new chat
- `--think-mode`: Enable Think mode
- `--deep-search`: Enable DeepSearch mode
- `--files`: Files to upload (can provide multiple)
- `--debug`: Enable debug mode
- `--save-api-response`: Save the raw API responses
- `--export-content`: Export response content to a text file
- `--log-level`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)

### Using the Chat Module

```python
import asyncio
from grok.chat import chat_with_grok

async def main():
    await chat_with_grok(
        debug_port=9222,
        message="Your message to Grok",
        new_chat=True,
        debug=True,
        log_level="DEBUG"  # Set detailed logging for debugging
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the Client (OpenAI-like Interface)

The client provides a more convenient, OpenAI-like interface:

```python
import asyncio
from grok.client import GrokClient, Message, FileAttachment

async def main():
    # Initialize the client with a specific log level
    client = GrokClient(debug_port=9222, log_level="INFO")
    
    # Simple query
    response = await client.chat_completion_async([
        Message(role="user", content="What is Python?")
    ])
    print(response.content)
    
    # With special modes and a different log level for this specific request
    response = await client.chat_completion_async(
        [
            Message(
                role="user", 
                content="Analyze the pros and cons of Python vs. JavaScript",
                think_mode=True,  # Enable Think mode
                deep_search=True  # Enable DeepSearch (web search)
            )
        ],
        log_level="DEBUG"  # Override log level for this request only
    )
    
    # With file attachment
    response = await client.chat_completion_async([
        Message(
            role="user",
            content="What is this file about?",
            attachments=[FileAttachment("path/to/file.pdf")]
        )
    ])

if __name__ == "__main__":
    asyncio.run(main())
```

## Example Scripts

The `examples/` directory contains ready-to-use example scripts:

- **one_shot.py**: Basic one-shot queries to Grok
- **multi_shot.py**: Multi-turn conversation with context
- **pdf_analysis.py**: PDF document analysis

Run them with:

```bash
python examples/one_shot.py
```

See the [examples README](examples/README.md) for more details.

## API Response Parser

The parser can handle two types of Grok API responses:

1. **Standard responses**: Single JSON objects
2. **Streaming responses**: Multiple concatenated JSON objects, each containing a token

### Features

- Robust parsing of streaming responses
- Token accumulation for complete text
- Detection of response completion
- Extraction of relevant metadata

## Running Tests

Run the parser tests:

```bash
python -m grok.parser.test_response_parser
```

Test with example files:

```bash
python -m grok.examples.test_parser
```

## License

[MIT](LICENSE)

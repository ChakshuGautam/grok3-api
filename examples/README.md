# Grok Client Examples

This directory contains examples of how to use the Grok API client.

## Available Examples

- **one_shot.py**: Demonstrates basic one-shot queries to Grok
- **multi_shot.py**: Shows how to maintain a conversation with multiple turns
- **pdf_analysis.py**: Example of analyzing PDF documents with Grok

## Running the Examples

Make sure you have Chrome running with remote debugging enabled:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

Then you can run any of the examples:

```bash
# Run the one-shot example
python examples/one_shot.py

# Run the multi-shot conversation example
python examples/multi_shot.py

# Run the PDF analysis example
python examples/pdf_analysis.py
```

## Using the GrokClient in Your Own Code

```python
import asyncio
from grok.client import GrokClient, Message, FileAttachment

async def main():
    # Initialize the client
    client = GrokClient(debug_port=9222, log_level="INFO")
    
    # Simple text query
    response = await client.chat_completion_async([
        Message(role="user", content="What is Python?")
    ])
    print(response.content)
    
    # With file attachment and DEBUG level logging for detailed diagnostics
    response = await client.chat_completion_async(
        [
            Message(
                role="user",
                content="What is this file about?",
                attachments=[FileAttachment("path/to/file.pdf")]
            )
        ],
        log_level="DEBUG"  # Override log level just for this request
    )
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Notes

- Each example adds the project root to the path to ensure imports work correctly
- The client automatically handles the interaction with the Grok API through Chrome
- For PDF analysis, keep file sizes reasonable (under 10MB) for best results
- Use the `log_level` parameter to control the verbosity of logging:
  - `DEBUG`: Detailed logs for diagnosing issues
  - `INFO`: Standard information about execution (default)
  - `WARNING`: Only warnings and more severe issues
  - `ERROR`: Only error messages
  - `CRITICAL`: Only critical issues 
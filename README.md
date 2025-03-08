# Grok 3 API Client

A Python client for interacting with Grok 3 via a Chrome browser with remote debugging.

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- `playwright` Python package (installed automatically with the project)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/grok3-api.git
   cd grok3-api
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Quick Start

### Step 1: Start Chrome with Remote Debugging Enabled

First, start Chrome with remote debugging enabled using the provided script:

```bash
./start_chrome.sh
```

This will open a new Chrome instance with remote debugging enabled on port 9222.

If you want to use a different port:

```bash
./start_chrome.sh --port 9223
```

### Step 2: Log into Grok

In the Chrome browser that was opened, navigate to [web.grok.chat](https://web.grok.chat) and log in with your Grok credentials.

### Step 3: Use the API client

Now you can use the Grok API client in your Python code:

```python
from grok.client import GrokClient, Message

# Initialize client (using the same port as in step 1)
client = GrokClient(debug_port=9222)

# Create a message
message = Message(role="user", content="What is Python?")

# Get response
response = client.chat_completion([message])

# Print the response
print(response.content)
```

For async usage:

```python
import asyncio
from grok.client import GrokClient, Message

async def main():
    # Initialize client
    client = GrokClient()
    
    # Create a message
    message = Message(role="user", content="What is Python?")
    
    # Get response
    response = await client.chat_completion_async([message])
    
    # Print the response
    print(response.content)

asyncio.run(main())
```

## Examples

Check the `examples` directory for more usage examples:

- `basic.py`: Simple chat completion example
- `streaming.py`: Streaming response example
- `multi_shot.py`: Maintaining conversation context (multi-turn)
- `file_upload.py`: Uploading files to Grok

## Error Troubleshooting

If you see an error like:

```
RuntimeError: Chat module failed with return code 1. Chrome is not running with remote debugging enabled.
```

Make sure:
1. Chrome is running with remote debugging enabled (run `./start_chrome.sh`)
2. You're using the correct debugging port 
3. You're logged into Grok in the Chrome browser

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

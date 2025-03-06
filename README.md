# Grok Chat Script

A simple Python client to interact with Grok using Playwright and an existing Chrome instance. Provides both command-line usage and a Python client similar to OpenAI's interface.

## Demo

https://github.com/user-attachments/assets/22b5e055-2a79-48c2-bf05-ce8d92ac049a

## TODO

- [ ] Add support for file uploads
- [ ] Add support for streaming responses
- [ ] Add support for DeepSearch mode
- [ ] Add support for Think mode
- [ ] Add support for other models
- [ ] Formatting of reponses

## Requirements

- Python 3.7+
- Playwright (`pip install playwright`)
- Chrome browser with remote debugging enabled

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/grok-chat.git
cd grok-chat
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install playwright
playwright install chromium
```

## Usage

### Command Line

1. Start Chrome with remote debugging enabled:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```
This cannot be run headless since you will need to click "Verify Human". When the browser opens, login to your Grok account and then run the script.

2. Run the script directly:
```bash
python grok_chat.py --message "Your message here"
```

Optional arguments:
- `--port`: Chrome remote debugging port (default: 9222)
- `--message`: Message to send to Grok (required)

### Python Client

The `GrokClient` class provides an OpenAI-like interface that uses `grok_chat.py` under the hood:

```python
from grok_client import GrokClient, Message

# Initialize client
client = GrokClient(debug_port=9222)

# One-shot completion
response = client.chat_completion([
    Message(role="user", content="Write a haiku about programming")
])
print(response.content)

# Multiple messages
messages = [
    Message(role="user", content="What is Python?")
]
response = client.chat_completion(messages)
print(response.content)

messages.extend([
    Message(role="assistant", content=response.content),
    Message(role="user", content="What are its main features?")
])
response = client.chat_completion(messages)
print(response.content)

# Async support
async def main():
    response = await client.chat_completion_async(messages)
    print(response.content)
```

Note: Currently, each message starts a new chat due to `grok_chat.py` limitations. Conversation history is maintained in the client but not sent to Grok.

## License

MIT License - See LICENSE file for details

# GrokClient Examples

This directory contains example scripts demonstrating different ways to use the GrokClient.

## Prerequisites

Make sure you have:
1. Chrome running with remote debugging enabled:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```
2. Grok website open and logged in

## Installation

1. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the package in development mode:
```bash
pip install -e .
```

## Examples

### 1. One-Shot Usage (`one_shot.py`)

Demonstrates independent, single-message interactions with Grok. Each request starts a new chat and gets a response.

```bash
python examples/one_shot.py
```

Features demonstrated:
- Generating creative content (haiku)
- Getting explanations
- Problem-solving queries

### 2. Multi-Shot Conversation (`multi_shot.py`)

Shows how to maintain a conversation context using multiple messages. While each message currently starts a new chat in Grok (due to limitations), the client maintains the conversation history.

```bash
python examples/multi_shot.py
```

Features demonstrated:
- Starting a conversation
- Adding responses to conversation history
- Asking follow-up questions
- Maintaining context on the client side
- Viewing full conversation history

## Notes

- Each example can be run independently
- The scripts use async/await for efficient communication
- All examples assume Chrome is running with remote debugging on port 9222
- Make sure you're logged into Grok before running the examples 
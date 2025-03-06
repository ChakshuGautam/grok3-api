#!/usr/bin/env python3
"""
Simple script to interact with Grok using Playwright.
Connects to an existing Chrome instance with remote debugging enabled.

Usage:
    python grok_chat.py --port 9222 --message "Your message here" [--new-chat]
"""

import asyncio
import argparse
import sys
from playwright.async_api import async_playwright, TimeoutError

# Constants
SELECTOR_TIMEOUT = 30000  # 30 seconds
RESPONSE_TIMEOUT = 60000  # 60 seconds
STABLE_CHECK_INTERVAL = 2  # seconds
MAX_STABLE_CHECKS = 5
MAX_RETRIES = 3

async def chat_with_grok(debug_port: int, message: str, new_chat: bool = False):
    async with async_playwright() as p:
        try:
            # Connect to existing Chrome instance
            print(f"Connecting to Chrome on port {debug_port}...", file=sys.stderr)
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
            
            # Get the first context
            context = browser.contexts[0]
            if not context:
                print("No browser context found. Make sure Chrome is running.", file=sys.stderr)
                return
            
            # Find or create Grok tab
            grok_page = None
            for page in context.pages:
                try:
                    if "grok.com" in page.url:
                        grok_page = page
                        print(f"Found existing Grok tab: {page.url}", file=sys.stderr)
                        break
                except:
                    continue
            
            if not grok_page:
                print("Creating new Grok tab...", file=sys.stderr)
                grok_page = await context.new_page()
                await grok_page.goto("https://grok.com")
                new_chat = True  # Force new chat if we created a new tab
            
            # Make sure we're on grok.com
            if not "grok.com" in grok_page.url:
                print("Navigating to grok.com...", file=sys.stderr)
                await grok_page.goto("https://grok.com")
                await asyncio.sleep(2)
                new_chat = True  # Force new chat if we had to navigate
            
            # Start new chat if requested
            if new_chat:
                print("Starting new chat...", file=sys.stderr)
                try:
                    new_chat_button = await grok_page.wait_for_selector('a[href="/chat"]', timeout=SELECTOR_TIMEOUT)
                    if new_chat_button:
                        await new_chat_button.click()
                        await asyncio.sleep(2)
                except TimeoutError:
                    print("Could not find new chat button. Assuming we're already in a chat.", file=sys.stderr)
            else:
                print("Continuing existing chat...", file=sys.stderr)
            
            # Find and fill input field
            print(f"Sending message: {message}", file=sys.stderr)
            try:
                input_field = await grok_page.wait_for_selector('textarea.w-full', timeout=SELECTOR_TIMEOUT)
                await input_field.fill(message)
            except TimeoutError:
                print("Could not find input field. Make sure you're logged into Grok.", file=sys.stderr)
                sys.exit(1)
            
            # Send message
            try:
                send_button = await grok_page.wait_for_selector('button[type="submit"]', timeout=SELECTOR_TIMEOUT)
                await send_button.click()
            except TimeoutError:
                print("Could not find send button.", file=sys.stderr)
                sys.exit(1)
            
            # Wait for and capture response
            print("\nWaiting for response...", file=sys.stderr)
            
            try:
                # Wait for message row to appear
                print("Waiting for message row...", file=sys.stderr)
                await grok_page.wait_for_selector('.message-row', timeout=RESPONSE_TIMEOUT)
                
                # Wait for actual content
                print("Waiting for content...", file=sys.stderr)
                await grok_page.wait_for_function(
                    """
                    () => {
                        const rows = document.querySelectorAll('.message-row');
                        const lastRow = rows[rows.length - 1];
                        if (!lastRow) return false;
                        const paragraphs = lastRow.querySelectorAll('p.break-words');
                        return paragraphs.length > 0 && Array.from(paragraphs).some(p => p.textContent.trim().length > 0);
                    }
                    """,
                    timeout=RESPONSE_TIMEOUT
                )
            except TimeoutError:
                print("Timed out waiting for response.", file=sys.stderr)
                sys.exit(1)
            
            # Monitor response until complete
            last_content = ""
            stable_count = 0
            retry_count = 0
            
            while stable_count < MAX_STABLE_CHECKS and retry_count < MAX_RETRIES:
                # Get current content
                content = await grok_page.evaluate(
                    """
                    () => {
                        const rows = document.querySelectorAll('.message-row');
                        const lastRow = rows[rows.length - 1];
                        if (!lastRow) return '';
                        
                        const paragraphs = Array.from(lastRow.querySelectorAll('p.break-words'));
                        const content = paragraphs
                            .map(p => p.textContent.trim())
                            .filter(text => text.length > 0)
                            .join('\\n\\n');
                        console.log('Current content:', content);  // Debug log
                        return content;
                    }
                    """
                )
                
                if not content:
                    retry_count += 1
                    print(f"No content found, retry {retry_count}/{MAX_RETRIES}", file=sys.stderr)
                    await asyncio.sleep(STABLE_CHECK_INTERVAL)
                    continue
                
                if content == last_content:
                    stable_count += 1
                    print(f"Response stable for {stable_count}/{MAX_STABLE_CHECKS} checks (length: {len(content)})", file=sys.stderr)
                else:
                    print(f"Response growing: {len(content)} chars", file=sys.stderr)
                    stable_count = 0
                    last_content = content
                
                await asyncio.sleep(STABLE_CHECK_INTERVAL)
            
            # Print final response
            if last_content:
                # Print to stdout for capturing by the client
                print("-" * 50)
                print(last_content)
                print("-" * 50)
            else:
                print("No response captured", file=sys.stderr)
                sys.exit(1)
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
        finally:
            # Don't close the browser since it's user's instance
            pass

def main():
    parser = argparse.ArgumentParser(description="Chat with Grok using an existing Chrome instance")
    parser.add_argument("--port", type=int, default=9222, help="Chrome remote debugging port")
    parser.add_argument("--message", type=str, required=True, help="Message to send to Grok")
    parser.add_argument("--new-chat", action="store_true", help="Start a new chat instead of continuing existing one")
    args = parser.parse_args()
    
    asyncio.run(chat_with_grok(args.port, args.message, args.new_chat))

if __name__ == "__main__":
    main() 
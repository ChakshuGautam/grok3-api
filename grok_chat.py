#!/usr/bin/env python3
"""
Simple script to interact with Grok using Playwright.
Connects to an existing Chrome instance with remote debugging enabled.

Usage:
    python grok_chat.py --port 9222 --message "Your message here" [--new-chat] [--think-mode] [--deep-search] [--files file1 file2 ...]
"""

import asyncio
import argparse
import sys
import json
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import mimetypes
from playwright.async_api import async_playwright, TimeoutError, Request, Response, Route
import logging
import os
import time
import re
from grok_response_parser import GrokResponseParser, parse_grok_response

# Constants
SELECTOR_TIMEOUT = 30000  # 30 seconds
RESPONSE_TIMEOUT = 60000  # 60 seconds
STABLE_CHECK_INTERVAL = 2  # seconds
MAX_STABLE_CHECKS = 5
MAX_RETRIES = 3
DEBUG_DIR = Path("debug")  # Debug directory
API_RESPONSE_PATTERN = r"https://grok\.com/rest/app-chat/conversations/[^/]+/responses"

# Set up logging
logger = logging.getLogger(__name__)

# Helper function to clear debug directory
def clear_debug_dir():
    if DEBUG_DIR.exists():
        logger.info(f"Clearing debug directory: {DEBUG_DIR}")
        shutil.rmtree(DEBUG_DIR)
    DEBUG_DIR.mkdir(exist_ok=True)
    logger.info(f"Created debug directory: {DEBUG_DIR}")

# Helper function to take screenshot
async def take_screenshot(page, name):
    timestamp = int(time.time())
    filename = f"{name}_{timestamp}.png"
    filepath = DEBUG_DIR / filename
    await page.screenshot(path=str(filepath))
    logger.info(f"Screenshot saved: {filepath}")
    return filepath

# Helper function to save HTML
async def save_html(page, name):
    timestamp = int(time.time())
    filename = f"{name}_{timestamp}.html"
    filepath = DEBUG_DIR / filename
    html_content = await page.content()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"HTML saved: {filepath}")
    return filepath

# Class to track API responses
class ApiResponseTracker:
    def __init__(self):
        self.api_responses: Dict[str, List[Dict[str, Any]]] = {}
        self.conversation_id: Optional[str] = None
        self.response_id: Optional[str] = None
        self.parser = GrokResponseParser()
    
    def extract_conversation_id(self, url: str) -> Optional[str]:
        return self.parser.extract_conversation_id(url)
    
    async def handle_response(self, response: Response) -> None:
        url = response.url
        
        # Check if this is a Grok API response URL
        if not re.match(API_RESPONSE_PATTERN, url):
            return
        
        # Extract conversation ID
        conversation_id = self.extract_conversation_id(url)
        if not conversation_id:
            logger.warning(f"Could not extract conversation ID from {url}")
            return
        
        self.conversation_id = conversation_id
        
        # Initialize list for this conversation if not exists
        if conversation_id not in self.api_responses:
            self.api_responses[conversation_id] = []
        
        try:
            # Get the response text
            response_text = await response.text()
            
            if not response_text:
                logger.debug("Empty response received")
                return
            
            # Store the raw response
            response_entry = {
                'timestamp': time.time(),
                'status': response.status,
                'content': response_text
            }
            self.api_responses[conversation_id].append(response_entry)
            
            # Process the response using our dedicated parser
            parse_result = self.parser.parse_response(response_text)
            
            if parse_result['success']:
                # Update response metadata
                if 'response_id' in parse_result and parse_result['response_id']:
                    self.response_id = parse_result['response_id']
                    response_entry['response_id'] = self.response_id
                
                # Add parsed data to the response entry
                response_entry['parsed'] = parse_result
                
                logger.debug(f"Successfully parsed API response from {url} (format: {parse_result['format']})")
            else:
                logger.debug(f"Failed to parse API response: {parse_result['message']}")
                
            logger.debug(f"Captured API response: {url} (size: {len(response_text)})")
        except Exception as e:
            logger.warning(f"Failed to process API response from {url}: {e}")
    
    def get_full_response(self, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the complete API response data for the given conversation"""
        conv_id = conversation_id or self.conversation_id
        
        if not conv_id or conv_id not in self.api_responses:
            return {
                'success': False,
                'message': 'No conversation data available',
                'data': None
            }
        
        responses = self.api_responses[conv_id]
        if not responses:
            return {
                'success': False,
                'message': 'No responses captured for this conversation',
                'data': None
            }
        
        # If we have accumulated tokens, return them
        if self.parser.accumulated_tokens:
            return {
                'success': True,
                'message': 'Full response retrieved from token stream',
                'data': {
                    'accumulated_text': self.parser.get_accumulated_text(),
                    'is_complete': self.parser.is_complete,
                    'response_id': self.response_id
                },
                'raw': responses[-1]['content'],
                'timestamp': responses[-1]['timestamp'],
                'status': responses[-1]['status'],
                'conversation_id': conv_id,
                'response_id': self.response_id,
                'tokens_count': len(self.parser.accumulated_tokens)
            }
        
        # Fallback: try to parse the last response
        last_response = responses[-1]
        
        if 'parsed' in last_response and last_response['parsed']['success']:
            # If we already parsed this response, return the parsed data
            return {
                'success': True,
                'message': 'Full response retrieved from parsed data',
                'data': last_response['parsed'],
                'raw': last_response['content'],
                'timestamp': last_response['timestamp'],
                'status': last_response['status'],
                'conversation_id': conv_id,
                'response_id': self.response_id
            }
        
        # Try to parse it one more time
        try:
            parse_result = parse_grok_response(last_response['content'])
            
            if parse_result['success']:
                return {
                    'success': True,
                    'message': 'Full response retrieved',
                    'data': parse_result,
                    'raw': last_response['content'],
                    'timestamp': last_response['timestamp'],
                    'status': last_response['status'],
                    'conversation_id': conv_id,
                    'response_id': self.response_id
                }
            else:
                return {
                    'success': False,
                    'message': parse_result['message'],
                    'data': None,
                    'raw': last_response['content'],
                    'timestamp': last_response['timestamp'],
                    'status': last_response['status'],
                    'conversation_id': conv_id,
                    'response_id': self.response_id
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error parsing response: {str(e)}',
                'data': None,
                'raw': last_response['content'],
                'timestamp': last_response['timestamp'],
                'status': last_response['status'],
                'conversation_id': conv_id,
                'response_id': self.response_id
            }
    
    def get_response_fields(self) -> Dict[str, Any]:
        """Extract and return important fields from the parsed response"""
        # If we have accumulated tokens, return structured data about them
        if self.parser.accumulated_tokens:
            return {
                'success': True,
                'conversation_id': self.conversation_id,
                'response_id': self.response_id,
                'is_complete': self.parser.is_complete,
                'content': self.parser.get_accumulated_text(),
                'token_count': len(self.parser.accumulated_tokens)
            }
        
        # Use the most recent response that has been parsed
        for responses in reversed(self.api_responses.get(self.conversation_id, [])):
            if 'parsed' in responses and responses['parsed']['success']:
                parsed = responses['parsed']
                
                # For standard responses with message content
                if 'data' in parsed and isinstance(parsed['data'], dict):
                    if 'response' in parsed['data']:
                        response_obj = parsed['data']['response']
                        
                        # Extract useful fields
                        result = {
                            'success': True,
                            'conversation_id': self.conversation_id,
                            'response_id': response_obj.get('responseId'),
                            'is_thinking': response_obj.get('isThinking', False),
                            'is_soft_stop': response_obj.get('isSoftStop', False),
                        }
                        
                        # Extract message content if available
                        if 'message' in response_obj and isinstance(response_obj['message'], dict):
                            message = response_obj['message']
                            if 'content' in message:
                                result['content'] = message['content']
                            
                            # Extract search results if available
                            if 'webSearchResults' in message:
                                result['web_search_results'] = message.get('webSearchResults', [])
                            
                            # Extract file attachments if available
                            if 'fileAttachments' in message:
                                result['file_attachments'] = message.get('fileAttachments', [])
                            
                            # Extract steps if available (for think mode)
                            if 'steps' in message:
                                result['steps'] = message.get('steps', [])
                        
                        return result
                
                # For streaming responses
                if 'text' in parsed:
                    return {
                        'success': True,
                        'conversation_id': self.conversation_id,
                        'response_id': parsed.get('response_id'),
                        'is_complete': parsed.get('is_complete', False),
                        'content': parsed['text'],
                        'token_count': parsed.get('token_count', 0)
                    }
        
        # No valid response found
        return {'success': False, 'message': 'No valid response data available'}
    
    def extract_content_text(self) -> str:
        """Extract just the text content from the response"""
        # For token-based responses, return the accumulated text
        if self.parser.accumulated_tokens:
            return self.parser.get_accumulated_text()
        
        # For standard response formats
        response_fields = self.get_response_fields()
        if not response_fields['success']:
            return ""
        
        # Return content if available
        if 'content' in response_fields:
            return response_fields['content']
        
        return ""
    
    def export_response_content(self, filename: Optional[str] = None) -> Optional[Path]:
        """Save just the response content to a file"""
        if not self.conversation_id:
            logger.warning("No conversation data available to export")
            return None
        
        content = self.extract_content_text()
        if not content:
            logger.warning("No content available to export")
            return None
        
        # Create filename if not provided
        if not filename:
            timestamp = int(time.time())
            filename = f"grok_response_{self.conversation_id}_{timestamp}.txt"
        
        filepath = DEBUG_DIR / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Response content saved to {filepath}")
        return filepath
    
    def save_responses(self, conversation_id: Optional[str] = None) -> Optional[Path]:
        """Save all API responses for debugging/analysis"""
        conv_id = conversation_id or self.conversation_id
        
        if not conv_id or conv_id not in self.api_responses:
            logger.warning("No API responses to save")
            return None
        
        # Create a timestamp
        timestamp = int(time.time())
        filename = f"grok_api_responses_{conv_id}_{timestamp}.json"
        filepath = DEBUG_DIR / filename
        
        response_data = {
            'conversation_id': conv_id,
            'response_id': self.response_id,
            'responses': self.api_responses[conv_id],
            'accumulated_text': self.parser.get_accumulated_text() if self.parser.accumulated_tokens else None,
            'tokens_count': len(self.parser.accumulated_tokens) if self.parser.accumulated_tokens else 0,
            'is_complete': self.parser.is_complete
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2)
        
        logger.info(f"API responses saved to {filepath}")
        return filepath

async def chat_with_grok(debug_port: int, message: str, new_chat: bool = False, think_mode: bool = False, deep_search: bool = False, files: List[Path] = None, debug: bool = False, save_api_response: bool = False, export_content: bool = False):
    # Configure logging based on debug mode
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        # Enable playwright debug logging
        if "DEBUG" not in os.environ:
            os.environ["DEBUG"] = "pw:api"
        
        # Clear debug directory
        clear_debug_dir()
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Create API tracker
    api_tracker = ApiResponseTracker()
    
    async with async_playwright() as p:
        try:
            logger.debug("Starting Playwright session")
            # Connect to existing Chrome instance
            logger.info(f"Connecting to Chrome on port {debug_port}...")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
            
            # Get the first context
            context = browser.contexts[0]
            if not context:
                logger.error("No browser context found. Make sure Chrome is running.")
                return
            
            # Find or create Grok tab
            grok_page = None
            for page in context.pages:
                try:
                    if "grok.com" in page.url:
                        grok_page = page
                        logger.info(f"Found existing Grok tab: {page.url}")
                        break
                except Exception as e:
                    logger.debug(f"Error checking page URL: {e}")
                    continue
            
            if not grok_page:
                logger.info("Creating new Grok tab...")
                grok_page = await context.new_page()
                await grok_page.goto("https://grok.com")
                new_chat = True  # Force new chat if we created a new tab
            
            # Set up API response interceptor
            logger.info("Setting up API response tracking...")
            grok_page.on("response", api_tracker.handle_response)
            
            # Make sure we're on grok.com
            if not "grok.com" in grok_page.url:
                logger.info("Navigating to grok.com...")
                await grok_page.goto("https://grok.com")
                await asyncio.sleep(2)
            
            if debug:
                await take_screenshot(grok_page, "initial_page")
                await save_html(grok_page, "initial_page")
            
            # Start a new chat if requested
            if new_chat:
                logger.info("Starting new chat...")
                try:
                    # Check if already in new chat (input area is visible)
                    input_visible = await grok_page.is_visible('div[data-testid="chat-composer"]')
                    if not input_visible:
                        # Look for new chat button and click it
                        new_chat_button = await grok_page.wait_for_selector('a[href="/chat"]', timeout=SELECTOR_TIMEOUT)
                        if new_chat_button:
                            await new_chat_button.click()
                            await asyncio.sleep(1)
                        
                    if debug:
                        await take_screenshot(grok_page, "new_chat")
                        await save_html(grok_page, "new_chat")
                except Exception as e:
                    logger.warning(f"Could not start new chat: {e}")
                    # Try to continue anyway
            
            # Upload files if provided
            if files:
                logger.info("Uploading files...")
                try:
                    # The file upload dialog might already be open
                    # Look for the "Select files" button directly in the dialog
                    if debug:
                        await take_screenshot(grok_page, "before_upload_attempt")
                        await save_html(grok_page, "before_upload_attempt")
                    
                    try:
                        # First check if the dialog with "Select files" is visible
                        select_files_button = await grok_page.wait_for_selector('button:has-text("Select files")', timeout=5000)
                        if select_files_button:
                            logger.info("Found 'Select files' button in already open dialog")
                            if debug:
                                await take_screenshot(grok_page, "select_files_button_found")
                    except TimeoutError:
                        # If not visible, we need to click the attachment button first
                        logger.info("Looking for attachment button")
                        try:
                            # This is the paperclip button in the chat interface
                            attach_button = await grok_page.wait_for_selector('button:has([d="M10 9V15C10 16.1046 10.8954 17 12 17V17C13.1046 17 14 16.1046 14 15V7C14 4.79086 12.2091 3 10 3V3C7.79086 3 6 4.79086 6 7V15C6 18.3137 8.68629 21 12 21V21C15.3137 21 18 18.3137 18 15V8"])', timeout=SELECTOR_TIMEOUT)
                            
                            if debug:
                                await take_screenshot(grok_page, "found_attach_button")
                            
                            await attach_button.click()
                            logger.info("Clicked attachment button")
                            
                            if debug:
                                await take_screenshot(grok_page, "after_attach_button_click")
                            
                            # Now wait for the dialog to appear with the "Select files" button
                            select_files_button = await grok_page.wait_for_selector('button:has-text("Select files")', timeout=SELECTOR_TIMEOUT)
                            if select_files_button:
                                logger.info("Found 'Select files' button after clicking attachment button")
                        except TimeoutError:
                            logger.error("Could not find attachment button")
                            if debug:
                                await take_screenshot(grok_page, "attach_button_error")
                                await save_html(grok_page, "attach_button_error")
                            sys.exit(1)
                    
                    # Click the "Select files" button
                    if select_files_button:
                        if debug:
                            await take_screenshot(grok_page, "before_select_files_click")
                        
                        # We need to find the hidden file input element that will be triggered
                        file_input = await grok_page.query_selector('input[type="file"]')
                        
                        if not file_input:
                            logger.warning("No file input found yet, trying to click 'Select files' button to reveal it")
                            await select_files_button.click()
                            logger.info("Clicked 'Select files' button")
                            
                            # Wait a bit for potential OS file dialogs to appear
                            await asyncio.sleep(1)
                            
                            # Try to find the file input again
                            file_input = await grok_page.query_selector('input[type="file"]')
                    else:
                        logger.error("Could not find 'Select files' button in dialog")
                        if debug:
                            await take_screenshot(grok_page, "select_files_button_error")
                            await save_html(grok_page, "select_files_button_error")
                        sys.exit(1)
                    
                    # Upload files through file input
                    if file_input:
                        file_paths = [str(f.absolute()) for f in files]
                        logger.info(f"Uploading files: {file_paths}")
                        
                        # Use the file_input's setInputFiles method directly
                        await file_input.set_input_files(file_paths)
                        
                        if debug:
                            await take_screenshot(grok_page, "after_file_set")
                            await save_html(grok_page, "after_file_set")
                        
                        await asyncio.sleep(2)  # Wait for upload to complete

                        # Check for uploaded files in recent files section
                        for file_path in files:
                            try:
                                # Look for the filename in the UI - it might be in the recent files section
                                await grok_page.wait_for_selector(f'span:has-text("{file_path.name}")', timeout=SELECTOR_TIMEOUT)
                                logger.info(f"Confirmed upload of {file_path.name}")
                                
                                if debug:
                                    await take_screenshot(grok_page, f"confirmed_upload_{file_path.name}")
                            except TimeoutError:
                                logger.error(f"Could not confirm upload of {file_path.name}")
                                
                                if debug:
                                    await take_screenshot(grok_page, f"upload_error_{file_path.name}")
                                    await save_html(grok_page, f"upload_error_{file_path.name}")
                        
                        # Try to click on the PDF file to select it if it's shown in the recent files list
                        try:
                            recent_file = await grok_page.wait_for_selector(f'div.bg-chip:has-text("{files[0].name}")', timeout=5000)
                            if recent_file:
                                logger.info(f"Found {files[0].name} in recent files list, clicking it")
                                await recent_file.click()
                                
                                if debug:
                                    await take_screenshot(grok_page, "selected_recent_file")
                        except TimeoutError:
                            logger.warning(f"Could not select {files[0].name} from recent files")

                        # Close the dialog if needed
                        try:
                            logger.info("Looking for close button...")
                            close_button = await grok_page.wait_for_selector('button:has(svg path[d="M18 6 6 18"])', timeout=5000)
                            if close_button:
                                await close_button.click()
                                logger.info("Closed dialog via X button")
                                await asyncio.sleep(1)
                                
                                if debug:
                                    await take_screenshot(grok_page, "after_close_dialog")
                        except TimeoutError:
                            logger.info("Could not find X close button")
                            
                            # Try the Escape key as an alternative
                            try:
                                await grok_page.keyboard.press("Escape")
                                logger.info("Pressed Escape to close dialog")
                                await asyncio.sleep(1)
                                
                                if debug:
                                    await take_screenshot(grok_page, "after_escape_key")
                            except Exception as e:
                                logger.warning(f"Could not press Escape key: {e}")
                    else:
                        logger.error("Could not find file input element")
                        if debug:
                            await take_screenshot(grok_page, "file_input_not_found")
                            await save_html(grok_page, "file_input_not_found")
                        sys.exit(1)

                except TimeoutError as e:
                    logger.error(f"Could not upload files: {str(e)}")
                    
                    if debug:
                        await take_screenshot(grok_page, "file_upload_timeout_error")
                        await save_html(grok_page, "file_upload_timeout_error")
                    
                    sys.exit(1)
                except Exception as e:
                    logger.error(f"Error during file upload: {str(e)}")
                    
                    if debug:
                        await take_screenshot(grok_page, "file_upload_general_error")
                        await save_html(grok_page, "file_upload_general_error")
                    
                    sys.exit(1)
            
            # Find and fill input field
            logger.info(f"Sending message: {message}")
            try:
                # Wait for the textarea to be available
                textarea = await grok_page.wait_for_selector('textarea.w-full', timeout=SELECTOR_TIMEOUT)
                
                if debug:
                    await take_screenshot(grok_page, "before_typing_message")
                
                # Type message
                await textarea.fill(message)
                await asyncio.sleep(1)
                
                if debug:
                    await take_screenshot(grok_page, "after_typing_message")
                
                # Enable Think mode if requested
                if think_mode:
                    logger.info("Enabling Think mode...")
                    try:
                        think_toggle = await grok_page.wait_for_selector('button[aria-label*="Think"]', timeout=5000)
                        if think_toggle:
                            await think_toggle.click()
                            logger.info("Think mode enabled")
                            
                            if debug:
                                await take_screenshot(grok_page, "think_mode_enabled")
                    except TimeoutError:
                        logger.warning("Could not find Think mode toggle")
                
                # Enable DeepSearch mode if requested
                if deep_search:
                    logger.info("Enabling DeepSearch mode...")
                    try:
                        deep_search_toggle = await grok_page.wait_for_selector('button[aria-label*="DeepSearch"]', timeout=5000)
                        if deep_search_toggle:
                            await deep_search_toggle.click()
                            logger.info("DeepSearch mode enabled")
                            
                            if debug:
                                await take_screenshot(grok_page, "deep_search_enabled")
                    except TimeoutError:
                        logger.warning("Could not find DeepSearch mode toggle")
                
                # Press Enter to send
                if debug:
                    await take_screenshot(grok_page, "before_sending")
                
                await textarea.press("Enter")
                logger.info("Message sent, waiting for response...")
                
                if debug:
                    await take_screenshot(grok_page, "after_sending")
                    await save_html(grok_page, "after_sending")
                
            except TimeoutError:
                logger.error("Could not find message input field")
                
                if debug:
                    await take_screenshot(grok_page, "input_field_error")
                    await save_html(grok_page, "input_field_error")
                
                sys.exit(1)
            
            # Wait for and capture response
            logger.info("\nWaiting for response...")
            
            try:
                # Wait for message row to appear
                logger.info("Waiting for message row...")
                await grok_page.wait_for_selector('.message-row', timeout=RESPONSE_TIMEOUT)
                
                # Wait for actual content
                logger.info("Waiting for content...")
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
                logger.error("Timed out waiting for response.")
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
                    logger.info(f"No content found, retry {retry_count}/{MAX_RETRIES}")
                    await asyncio.sleep(STABLE_CHECK_INTERVAL)
                    continue
                
                if content == last_content:
                    stable_count += 1
                    logger.info(f"Response stable for {stable_count}/{MAX_STABLE_CHECKS} checks (length: {len(content)})")
                else:
                    logger.info(f"Response growing: {len(content)} chars")
                    stable_count = 0
                    last_content = content
                
                await asyncio.sleep(STABLE_CHECK_INTERVAL)
            
            # Retrieve the full API response
            logger.info("Retrieving full API response...")
            api_response = api_tracker.get_full_response()
            
            if api_response['success']:
                logger.info(f"Successfully captured API response for conversation: {api_tracker.conversation_id}")
                
                # Get structured fields from the response
                response_fields = api_tracker.get_response_fields()
                if response_fields['success']:
                    logger.info(f"Response ID: {response_fields.get('response_id')}")
                    
                    # For token-based responses
                    if 'token_count' in response_fields:
                        logger.info(f"Tokens captured: {response_fields.get('token_count')}")
                        logger.info(f"Response complete: {response_fields.get('is_complete', False)}")
                    else:
                        # For standard responses
                        logger.info(f"Is thinking: {response_fields.get('is_thinking')}")
                        logger.info(f"Is soft stop: {response_fields.get('is_soft_stop')}")
                
                # Save API responses if requested or in debug mode
                if save_api_response or debug:
                    api_response_file = api_tracker.save_responses()
                    if api_response_file:
                        logger.info(f"Full API responses saved to: {api_response_file}")
                
                # Export just the response content if requested
                if export_content:
                    content_file = api_tracker.export_response_content()
                    if content_file:
                        logger.info(f"Response content exported to: {content_file}")
            else:
                logger.warning(f"Failed to capture API response: {api_response['message']}")
            
            # Print final response
            if last_content:
                # Print to stdout for capturing by the client
                logger.info("-" * 50)
                logger.info(last_content)
                logger.info("-" * 50)
                
                # Print API response data if available
                if api_response['success'] and api_response['data']:
                    logger.info("API Response Data:")
                    logger.info("-" * 50)
                    
                    # Print structured fields first
                    if 'success' in response_fields and response_fields['success']:
                        logger.info("Structured Response Fields:")
                        for key, value in response_fields.items():
                            if key != 'success' and key != 'message' and key not in ['web_search_results', 'file_attachments', 'steps']:
                                logger.info(f"  {key}: {value}")
                        
                        # Print count of search results if any
                        if 'web_search_results' in response_fields and response_fields['web_search_results']:
                            logger.info(f"  web_search_results: {len(response_fields['web_search_results'])} items")
                        
                        # Print count of file attachments if any
                        if 'file_attachments' in response_fields and response_fields['file_attachments']:
                            logger.info(f"  file_attachments: {len(response_fields['file_attachments'])} items")
                    
                    # For token stream responses
                    if 'accumulated_text' in api_response['data']:
                        logger.info("Accumulated Response Text:")
                        logger.info(api_response['data']['accumulated_text'])
                    
                    # Print raw JSON data if in debug mode
                    if debug:
                        logger.info("Raw Response JSON:")
                        logger.info(json.dumps(api_response['data'], indent=2))
                    
                    logger.info("-" * 50)
            # If no displayed content but we have accumulated tokens, show those
            elif api_tracker.parser.accumulated_tokens:
                accumulated_text = api_tracker.parser.get_accumulated_text()
                logger.info("-" * 50)
                logger.info("Response from accumulated tokens:")
                logger.info(accumulated_text)
                logger.info("-" * 50)
            else:
                logger.error("No response captured")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error in chat_with_grok: {e}")
            sys.exit(1)
            
        finally:
            # Don't close the browser since it's user's instance
            pass

def main():
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
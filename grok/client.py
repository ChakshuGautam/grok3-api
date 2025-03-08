from typing import List, Optional, Union, Dict, Any
import asyncio
import os
import logging
from dataclasses import dataclass
from pathlib import Path
import sys
import tempfile

# Import chat module directly
from .chat import chat_with_grok, ApiResponseTracker

# Set up logging with console handler
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

@dataclass
class FileAttachment:
    path: Union[str, Path]  # Local file path
    name: Optional[str] = None  # Optional display name
    content_type: Optional[str] = None  # Optional MIME type

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.name:
            self.name = self.path.name
        if not self.content_type:
            import mimetypes
            self.content_type = mimetypes.guess_type(self.path)[0] or 'application/octet-stream'

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str
    think_mode: bool = False
    deep_search: bool = False
    attachments: List[FileAttachment] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []

class GrokResponse:
    def __init__(self, content: str, is_streaming: bool = False, is_complete: bool = True, response_id: Optional[str] = None, is_thinking: bool = False, is_soft_stop: bool = False):
        self.content = content
        self.is_streaming = is_streaming
        self.is_complete = is_complete
        self.response_id = response_id
        self.is_thinking = is_thinking
        self.is_soft_stop = is_soft_stop
        self.choices = [{"message": {"role": "assistant", "content": content}}]

    def __str__(self):
        return self.content

class GrokStreamResponse(GrokResponse):
    """Response object for streaming mode that contains a single token."""
    def __init__(self, token: str, is_complete: bool = False, response_id: Optional[str] = None, is_thinking: bool = False, is_soft_stop: bool = False):
        super().__init__(
            content=token,
            is_streaming=True,
            is_complete=is_complete,
            response_id=response_id,
            is_thinking=is_thinking,
            is_soft_stop=is_soft_stop
        )

class GrokClient:
    def __init__(self, debug_port: int = 9222, debug_mode: bool = False, log_level: str = "INFO"):
        """
        Initialize the Grok client.
        
        Args:
            debug_port: Chrome remote debugging port (default: 9222)
            debug_mode: Enable debug mode with verbose logging (default: False)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)
        """
        self.debug_port = debug_port
        self.debug_mode = debug_mode
        self.log_level = log_level
        logger.info(f"Using direct chat module communication")

    async def _run_grok_chat_nonstream(self, message: str, new_chat: bool = False, think_mode: bool = False, deep_search: bool = False, files: List[Path] = None) -> GrokResponse:
        """Run grok chat module with the given message in non-streaming mode."""
        logger.info(f"Running chat with message: {message} (new_chat: {new_chat}, think_mode: {think_mode}, deep_search: {deep_search}, files: {files})")
        
        try:
            # Create a temp file to capture output if needed
            temp_output_file = None
            if self.debug_mode:
                temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                logger.info(f"Debug mode enabled, will save API response to {temp_output_file.name}")
            
            # Call chat_with_grok directly
            api_tracker = ApiResponseTracker()
            
            # Use the chat_with_grok function directly
            await chat_with_grok(
                debug_port=self.debug_port,
                message=message,
                new_chat=new_chat,
                think_mode=think_mode,
                deep_search=deep_search,
                files=files,
                debug=self.debug_mode,
                save_api_response=True,
                export_content=False,
                log_level=self.log_level,
                stream=False,
                api_tracker=api_tracker  # Pass the API tracker
            )
            
            # Check if we have a response
            if not api_tracker.is_response_complete():
                logger.warning("Response is not complete")
            
            # Extract the response content
            content = api_tracker.extract_content_text()
            
            # Get the metadata
            response_fields = api_tracker.get_response_fields()
            
            logger.info(f"Successfully received chat response of length: {len(content)}")
            
            # Return the response
            return GrokResponse(
                content=content,
                is_streaming=False,
                is_complete=response_fields.get('is_complete', True),
                response_id=response_fields.get('response_id'),
                is_thinking=response_fields.get('is_thinking', False),
                is_soft_stop=response_fields.get('is_soft_stop', False)
            )

        except Exception as e:
            logger.error(f"Error running chat: {str(e)}")
            raise

    async def _run_grok_chat_stream(self, message: str, new_chat: bool = False, think_mode: bool = False, deep_search: bool = False, files: List[Path] = None):
        """Run grok chat module with the given message in streaming mode."""
        logger.info(f"Running chat stream with message: {message} (new_chat: {new_chat}, think_mode: {think_mode}, deep_search: {deep_search}, files: {files})")
        
        try:
            # Create a shared API tracker
            api_tracker = ApiResponseTracker()
            api_tracker.enable_streaming()  # Enable streaming mode
            
            # Start a background task to run the chat
            chat_task = asyncio.create_task(
                chat_with_grok(
                    debug_port=self.debug_port,
                    message=message,
                    new_chat=new_chat,
                    think_mode=think_mode,
                    deep_search=deep_search,
                    files=files,
                    debug=self.debug_mode,
                    save_api_response=True,
                    export_content=False,
                    log_level=self.log_level,
                    stream=True,
                    api_tracker=api_tracker  # Pass the API tracker
                )
            )
            
            # Now yield tokens as they're received
            previous_length = 0
            response_id = None
            
            # Keep yielding until the response is complete or chat_task is done
            while not api_tracker.is_response_complete() and not chat_task.done():
                # Get the current accumulated text
                accumulated_text = api_tracker.parser.get_accumulated_text()
                
                # Extract new tokens
                if len(accumulated_text) > previous_length:
                    new_token = accumulated_text[previous_length:]
                    previous_length = len(accumulated_text)
                    
                    # Get the metadata
                    response_fields = api_tracker.get_response_fields()
                    response_id = response_fields.get('response_id')
                    
                    # Yield the new token
                    yield GrokStreamResponse(
                        token=new_token,
                        is_complete=response_fields.get('is_complete', False),
                        response_id=response_id,
                        is_thinking=response_fields.get('is_thinking', False),
                        is_soft_stop=response_fields.get('is_soft_stop', False)
                    )
                
                # Small sleep to avoid CPU spinning
                await asyncio.sleep(0.1)
            
            # Final check for any remaining content
            accumulated_text = api_tracker.parser.get_accumulated_text()
            if len(accumulated_text) > previous_length:
                new_token = accumulated_text[previous_length:]
                response_fields = api_tracker.get_response_fields()
                
                yield GrokStreamResponse(
                    token=new_token,
                    is_complete=True,
                    response_id=response_id,
                    is_thinking=response_fields.get('is_thinking', False),
                    is_soft_stop=response_fields.get('is_soft_stop', False)
                )
            
            # Ensure the chat task completes
            try:
                await chat_task
            except Exception as e:
                logger.error(f"Chat task error: {str(e)}")
                raise
        
        except Exception as e:
            logger.error(f"Error running chat stream: {str(e)}")
            raise

    async def chat_completion_async(
        self, 
        messages: List[Message],
        new_chat: bool = True,
        log_level: Optional[str] = None,
        stream: bool = False
    ):
        """
        Send a message to Grok and get a response, similar to OpenAI's chat completion.
        
        Args:
            messages: List of Message objects containing the conversation history
            new_chat: Whether to start a new chat (True) or continue existing (False)
            log_level: Override the logging level for this request (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            stream: Whether to use streaming mode for the response (default: False)
        
        Returns:
            If stream=True: An async generator yielding GrokStreamResponse objects
            If stream=False: A GrokResponse object containing the complete response
        """
        if stream:
            return self.chat_completion_async_stream(messages, new_chat, log_level)
        else:
            return await self.chat_completion_async_nonstream(messages, new_chat, log_level)

    async def chat_completion_async_nonstream(
        self, 
        messages: List[Message],
        new_chat: bool = True,
        log_level: Optional[str] = None
    ) -> GrokResponse:
        """
        Non-streaming implementation of chat_completion_async.
        
        Args:
            messages: List of Message objects containing the conversation history
            new_chat: Whether to start a new chat (True) or continue existing (False)
            log_level: Override the logging level for this request (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            A GrokResponse object containing the complete response
        """
        # For now, we only send the last user message
        # TODO: Implement conversation history support when chat module supports it
        last_message = messages[-1]
        if last_message.role != "user":
            raise ValueError("Last message must be from user")

        # Save current log_level to restore if needed
        current_log_level = self.log_level
        try:
            # Override log_level if provided
            if log_level:
                self.log_level = log_level
                
            # Convert file attachments to paths
            files = None
            if last_message.attachments:
                files = [attachment.path for attachment in last_message.attachments]

            # In non-streaming mode, use _run_grok_chat_nonstream which returns a GrokResponse
            return await self._run_grok_chat_nonstream(
                last_message.content,
                new_chat,
                last_message.think_mode,
                last_message.deep_search,
                files
            )
                
        finally:
            # Restore original log_level
            if log_level:
                self.log_level = current_log_level

    async def chat_completion_async_stream(
        self, 
        messages: List[Message],
        new_chat: bool = True,
        log_level: Optional[str] = None
    ):
        """
        Streaming implementation of chat_completion_async.
        
        Args:
            messages: List of Message objects containing the conversation history
            new_chat: Whether to start a new chat (True) or continue existing (False)
            log_level: Override the logging level for this request (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            An async generator yielding GrokStreamResponse objects
        """
        # For now, we only send the last user message
        # TODO: Implement conversation history support when chat module supports it
        last_message = messages[-1]
        if last_message.role != "user":
            raise ValueError("Last message must be from user")

        # Save current log_level to restore if needed
        current_log_level = self.log_level
        try:
            # Override log_level if provided
            if log_level:
                self.log_level = log_level
                
            # Convert file attachments to paths
            files = None
            if last_message.attachments:
                files = [attachment.path for attachment in last_message.attachments]

            # In streaming mode, use _run_grok_chat_stream which returns an async generator
            async for chunk in self._run_grok_chat_stream(
                last_message.content,
                new_chat,
                last_message.think_mode,
                last_message.deep_search,
                files
            ):
                yield chunk
                
        finally:
            # Restore original log_level
            if log_level:
                self.log_level = current_log_level

    def chat_completion(
        self, 
        messages: List[Message],
        new_chat: bool = True,
        log_level: Optional[str] = None,
        stream: bool = False
    ) -> GrokResponse:
        """
        Synchronous version of chat_completion_async.
        Note: Streaming mode is not supported in the synchronous version.
        
        Args:
            messages: List of Message objects containing the conversation history
            new_chat: Whether to start a new chat (True) or continue existing (False)
            log_level: Override the logging level for this request (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            stream: Whether to use streaming mode (not supported in sync version)
            
        Returns:
            GrokResponse object containing the complete response
        """
        if stream:
            raise ValueError("Streaming mode is not supported in synchronous chat_completion. Use chat_completion_async instead.")
        
        return asyncio.run(self.chat_completion_async_nonstream(messages, new_chat, log_level))

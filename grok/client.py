from typing import List, Optional, Union, Dict, Any
import asyncio
import subprocess
import os
import logging
from dataclasses import dataclass
from pathlib import Path
import sys

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
        # The script is now the module, so we'll use the module path
        self._module_name = "grok.chat"
        logger.info(f"Using grok.chat module for communication")

    async def _run_grok_chat_nonstream(self, message: str, new_chat: bool = False, think_mode: bool = False, deep_search: bool = False, files: List[Path] = None) -> GrokResponse:
        """Run grok chat module with the given message in non-streaming mode."""
        logger.info(f"Running chat with message: {message} (new_chat: {new_chat}, think_mode: {think_mode}, deep_search: {deep_search}, files: {files})")
        
        try:
            # Build command to run the module directly
            cmd = [
                sys.executable, '-m', self._module_name,
                '--port', str(self.debug_port),
                '--message', message,
                '--log-level', self.log_level,
                '--save-api-response'  # Always save API response for metadata
            ]
            if new_chat:
                cmd.append('--new-chat')
            if think_mode:
                cmd.append('--think-mode')
            if deep_search:
                cmd.append('--deep-search')
            if self.debug_mode:
                cmd.append('--debug')
            if files:
                cmd.append('--files')
                cmd.extend([str(f) for f in files])
            
            logger.info(f"Executing command: {' '.join(cmd)}")
                
            # Create process with line buffering
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Force Python to be unbuffered
            )
            
            # For non-streaming mode, collect full output
            full_output = []
            error_output = []
            api_response_data = {}
            
            # Read stdout and stderr concurrently
            async def read_stream(stream, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line = line.decode().rstrip()
                    if is_stderr:
                        logger.warning(f"stderr: {line}")
                        error_output.append(line)
                    else:
                        # Store stdout for later parsing
                        full_output.append(line)
                        # Check for API response data
                        if line.startswith("API Response Data:"):
                            # Parse API response data
                            api_data_start = full_output.index(line)
                            for i in range(api_data_start + 1, len(full_output)):
                                data_line = full_output[i]
                                if data_line.startswith("  "):  # API response field
                                    try:
                                        key, value = data_line.strip().split(": ", 1)
                                        api_response_data[key] = value
                                    except ValueError:
                                        continue

            # Read both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout),
                read_stream(process.stderr, True)
            )
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode != 0:
                error_msg = f"Chat module failed with return code {process.returncode}"
                detailed_error = "\n".join(error_output)
                logger.error(f"Error details:\n{detailed_error}")
                
                # Check for common chrome error patterns
                if any("Failed to connect to Chrome" in line for line in error_output) or \
                   any("Connection refused" in line for line in error_output) or \
                   any("connect_over_cdp" in line for line in error_output):
                    raise RuntimeError(f"{error_msg}. Chrome is not running with remote debugging enabled. "
                                      f"Please start Chrome with: "
                                      f"'chrome --remote-debugging-port={self.debug_port}' or "
                                      f"'/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={self.debug_port}'")
                else:
                    raise RuntimeError(f"{error_msg}. Error details: {detailed_error}")

            logger.info("Successfully ran chat")
            
            # Parse the output to extract Grok's response
            output = '\n'.join(full_output)
            try:
                # Find the response between the marker lines
                start_marker = "-" * 50 + "\n"
                end_marker = "\n" + "-" * 50
                response_start = output.index(start_marker) + len(start_marker)
                response_end = output.index(end_marker)
                response = output[response_start:response_end].strip()
                logger.info(f"Extracted response of length: {len(response)}")
                
                # Return complete response
                return GrokResponse(
                    content=response,
                    is_streaming=False,
                    is_complete=api_response_data.get('is_complete', 'True') == 'True',
                    response_id=api_response_data.get('response_id'),
                    is_thinking=api_response_data.get('is_thinking', 'False') == 'True',
                    is_soft_stop=api_response_data.get('is_soft_stop', 'False') == 'True'
                )
            except ValueError:
                # If markers not found, log the full output and return it
                logger.warning("Could not find response markers, returning full output")
                logger.debug(f"Full output: {output}")
                return GrokResponse(
                    content=output.strip(),
                    is_streaming=False,
                    is_complete=True,
                    response_id=None,
                    is_thinking=False,
                    is_soft_stop=False
                )

        except Exception as e:
            logger.error(f"Error running chat: {str(e)}")
            raise

    async def _run_grok_chat_stream(self, message: str, new_chat: bool = False, think_mode: bool = False, deep_search: bool = False, files: List[Path] = None):
        """Run grok chat module with the given message in streaming mode."""
        logger.info(f"Running chat stream with message: {message} (new_chat: {new_chat}, think_mode: {think_mode}, deep_search: {deep_search}, files: {files})")
        
        try:
            # Build command to run the module directly
            cmd = [
                sys.executable, '-m', self._module_name,
                '--port', str(self.debug_port),
                '--message', message,
                '--log-level', self.log_level,
                '--save-api-response',  # Always save API response for metadata
                '--stream'  # Always include stream flag for this method
            ]
            if new_chat:
                cmd.append('--new-chat')
            if think_mode:
                cmd.append('--think-mode')
            if deep_search:
                cmd.append('--deep-search')
            if self.debug_mode:
                cmd.append('--debug')
            if files:
                cmd.append('--files')
                cmd.extend([str(f) for f in files])

            logger.info(f"Executing command: {' '.join(cmd)}")

            # Create process with line buffering
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Force Python to be unbuffered
            )

            # For streaming mode, yield tokens as they arrive
            response_id = None
            is_complete = False
            is_thinking = False
            is_soft_stop = False
            error_output = []
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line = line.decode().rstrip()
                
                # Check for API response data
                if line.startswith("API Response Data:"):
                    continue
                elif line.startswith("  "):  # API response field
                    try:
                        key, value = line.strip().split(": ", 1)
                        if key == "response_id":
                            response_id = value
                        elif key == "is_complete":
                            is_complete = value == "True"
                        elif key == "is_thinking":
                            is_thinking = value == "True"
                        elif key == "is_soft_stop":
                            is_soft_stop = value == "True"
                    except ValueError:
                        continue
                else:
                    # Check if this is a response token
                    if line and not line.startswith("-" * 50):
                        yield GrokStreamResponse(
                            token=line,
                            is_complete=is_complete,
                            response_id=response_id,
                            is_thinking=is_thinking,
                            is_soft_stop=is_soft_stop
                        )
            
            # Read any remaining stderr
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                decoded_line = line.decode().rstrip()
                logger.warning(f"stderr: {decoded_line}")
                error_output.append(decoded_line)
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode != 0:
                error_msg = f"Chat module failed with return code {process.returncode}"
                detailed_error = "\n".join(error_output)
                logger.error(f"Error details:\n{detailed_error}")
                
                # Check for common chrome error patterns
                if any("Failed to connect to Chrome" in line for line in error_output) or \
                   any("Connection refused" in line for line in error_output) or \
                   any("connect_over_cdp" in line for line in error_output):
                    raise RuntimeError(f"{error_msg}. Chrome is not running with remote debugging enabled. "
                                      f"Please start Chrome with: "
                                      f"'chrome --remote-debugging-port={self.debug_port}' or "
                                      f"'/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={self.debug_port}'")
                else:
                    raise RuntimeError(f"{error_msg}. Error details: {detailed_error}")
        
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

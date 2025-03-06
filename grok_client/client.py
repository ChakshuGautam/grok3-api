from typing import List, Optional
import asyncio
import subprocess
import os
import logging
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str

class GrokResponse:
    def __init__(self, content: str):
        self.content = content
        self.choices = [{"message": {"role": "assistant", "content": content}}]

    def __str__(self):
        return self.content

class GrokClient:
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self._script_path = os.path.join(os.path.dirname(__file__), '..', 'grok_chat.py')
        if not os.path.exists(self._script_path):
            raise FileNotFoundError(f"Could not find grok_chat.py at {self._script_path}")
        logger.info(f"Using grok_chat.py at: {self._script_path}")

    async def _run_grok_chat(self, message: str, new_chat: bool = False) -> str:
        """Run grok_chat.py with the given message."""
        logger.info(f"Running grok_chat.py with message: {message} (new_chat: {new_chat})")
        
        try:
            cmd = [
                'python', self._script_path,
                '--port', str(self.debug_port),
                '--message', message
            ]
            if new_chat:
                cmd.append('--new-chat')

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            if stderr_text:
                logger.warning(f"stderr from grok_chat.py: {stderr_text}")
            
            if process.returncode != 0:
                error_msg = f"grok_chat.py failed with return code {process.returncode}"
                if stderr_text:
                    error_msg += f"\nError: {stderr_text}"
                if stdout_text:
                    error_msg += f"\nOutput: {stdout_text}"
                raise RuntimeError(error_msg)

            logger.info("Successfully ran grok_chat.py")
            
            # Parse the output to extract Grok's response
            output = stdout_text
            try:
                # Find the response between the marker lines
                start_marker = "-" * 50 + "\n"
                end_marker = "\n" + "-" * 50
                response_start = output.index(start_marker) + len(start_marker)
                response_end = output.index(end_marker)
                response = output[response_start:response_end].strip()
                logger.info(f"Extracted response of length: {len(response)}")
                return response
            except ValueError:
                # If markers not found, log the full output and return it
                logger.warning("Could not find response markers, returning full output")
                logger.debug(f"Full output: {output}")
                return output.strip()

        except Exception as e:
            logger.error(f"Error running grok_chat.py: {str(e)}")
            raise

    async def chat_completion_async(
        self, 
        messages: List[Message],
        new_chat: bool = True
    ) -> GrokResponse:
        """
        Send a message to Grok and get a response, similar to OpenAI's chat completion.
        
        Args:
            messages: List of Message objects containing the conversation history
            new_chat: Whether to start a new chat (True) or continue existing (False)
        
        Returns:
            GrokResponse object containing the assistant's response
        """
        # For now, we only send the last user message
        # TODO: Implement conversation history support when grok_chat.py supports it
        last_message = messages[-1]
        if last_message.role != "user":
            raise ValueError("Last message must be from user")

        try:
            response_text = await self._run_grok_chat(last_message.content, new_chat)
            if not response_text:
                logger.warning("Received empty response from Grok")
            return GrokResponse(response_text)
        except Exception as e:
            logger.error(f"Error in chat_completion_async: {str(e)}")
            raise

    def chat_completion(
        self, 
        messages: List[Message],
        new_chat: bool = True
    ) -> GrokResponse:
        """Synchronous version of chat_completion_async."""
        return asyncio.run(self.chat_completion_async(messages, new_chat)) 
#!/usr/bin/env python3
"""
Parser for Grok API responses that handles both standard and streaming formats.
The parser can handle multiple concatenated JSON objects in streaming format.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple, Iterator


class GrokResponseParser:
    """Parser for Grok API responses supporting both standard and streaming formats."""
    
    def __init__(self):
        self.accumulated_tokens: List[str] = []
        self.response_id: Optional[str] = None
        self.is_complete: bool = False
        self.streaming_mode: bool = False
    
    def reset(self):
        """Reset the parser state."""
        self.accumulated_tokens = []
        self.response_id = None
        self.is_complete = False
    
    def enable_streaming_mode(self):
        """Enable streaming mode for the parser"""
        self.streaming_mode = True
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse a Grok API response and return structured data.
        
        Args:
            response_text: The raw response text from the Grok API
            
        Returns:
            A dictionary with parsed response data
        """
        # First try to parse as a single JSON object
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                # It's a valid JSON object, process it
                self._process_json_object(data)
                return {
                    'success': True,
                    'format': 'standard',
                    'data': data,
                    'tokens': self.accumulated_tokens,
                    'response_id': self.response_id,
                    'is_complete': self.is_complete,
                    'token_count': len(self.accumulated_tokens)
                }
        except json.JSONDecodeError:
            pass
        
        # Try to parse as streaming format (concatenated JSON objects)
        chunks = list(self._split_json_chunks(response_text))
        
        if not chunks:
            return {
                'success': False,
                'format': 'unknown',
                'message': 'Could not parse response as JSON',
                'raw': response_text[:200] + ('...' if len(response_text) > 200 else '')
            }
        
        # Process each chunk
        valid_chunks = []
        for chunk in chunks:
            try:
                data = json.loads(chunk)
                self._process_json_object(data)
                valid_chunks.append(data)
            except json.JSONDecodeError:
                continue
        
        return {
            'success': len(valid_chunks) > 0,
            'format': 'streaming',
            'chunks_count': len(chunks),
            'valid_chunks_count': len(valid_chunks),
            'tokens': self.accumulated_tokens,
            'text': self.get_accumulated_text(),
            'response_id': self.response_id,
            'is_complete': self.is_complete,
            'token_count': len(self.accumulated_tokens)
        }
    
    def _process_json_object(self, data: Dict[str, Any]) -> None:
        """
        Process a single JSON object and extract relevant information.
        
        Args:
            data: A parsed JSON object
        """
        # Check if it's a result object with a token
        if 'result' in data:
            result = data['result']
            
            # Update response ID
            if 'responseId' in result:
                self.response_id = result['responseId']
            
            # Check if we have a token
            if 'token' in result:
                token = result['token']
                self.accumulated_tokens.append(token)
                
                # Check for completion markers
                if 'isSoftStop' in result and result['isSoftStop']:
                    self.is_complete = True
                    
            # Alternative completion indicators
            # 1. Empty token can sometimes indicate completion
            elif 'token' in result and result['token'] == "":
                self.is_complete = True
                
            # 2. Explicit completion flag
            if 'isComplete' in result and result['isComplete']:
                self.is_complete = True
                
            # 3. Final message structure may indicate completion
            if 'message' in result and isinstance(result['message'], dict):
                # If there's a complete message object, it's likely the final response
                self.is_complete = True
        
        # If it's a more complete response, store it
        self.parsed_response = data
        
    def is_response_complete(self) -> bool:
        """
        Check if the response stream is complete.
        
        Returns:
            True if the response is determined to be complete, False otherwise
        """
        # Return the stored completion state
        if self.is_complete:
            return True
            
        # Check for other completion indicators in the last few chunks
        if self.accumulated_tokens:
            # If no new tokens received in a while, this is a heuristic for completion
            # This would be implemented by the caller tracking time since last token
            
            # Sometimes the last few tokens indicate completion (e.g., ending punctuation)
            last_token = self.accumulated_tokens[-1] if self.accumulated_tokens else ""
            if last_token and last_token.strip() in [".", "!", "?", "\n"]:
                # Common ending punctuation can sometimes indicate completion
                # This is a heuristic and not always reliable
                return True
                
        return False
    
    def _split_json_chunks(self, text: str) -> Iterator[str]:
        """
        Split concatenated JSON objects into individual chunks.
        
        Args:
            text: Text containing potentially multiple JSON objects
            
        Returns:
            An iterator of JSON object strings
        """
        depth = 0
        start = None
        
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    # We found a complete JSON object
                    yield text[start:i+1]
                    start = None
    
    def get_accumulated_text(self) -> str:
        """Get the complete text from accumulated tokens."""
        return ''.join(self.accumulated_tokens)
    
    @staticmethod
    def extract_conversation_id(url: str) -> Optional[str]:
        """
        Extract conversation ID from a Grok API URL.
        
        Args:
            url: The Grok API URL
            
        Returns:
            The conversation ID if found, None otherwise
        """
        # Check for the ongoing conversation response pattern
        match = re.search(r"conversations/([^/]+)/responses", url)
        if match:
            return match.group(1)
            
        # Check for the new conversation pattern - may contain ID in response body, not URL
        if re.search(r"conversations/new", url):
            return "new"
            
        return None


def parse_grok_response(response_text: str) -> Dict[str, Any]:
    """
    Convenience function to parse a Grok API response without 
    maintaining parser state between calls.
    
    Args:
        response_text: The raw response text from the Grok API
        
    Returns:
        A dictionary with parsed response data
    """
    parser = GrokResponseParser()
    return parser.parse_response(response_text) 
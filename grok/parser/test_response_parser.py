#!/usr/bin/env python3
"""
Tests for the GrokResponseParser class.
"""

import unittest
import json
from grok.parser.response_parser import GrokResponseParser, parse_grok_response


class TestGrokResponseParser(unittest.TestCase):
    def setUp(self):
        self.parser = GrokResponseParser()
        
        # Sample of concatenated JSON objects from streaming response
        self.streaming_sample = """{
    "result": {
        "token": " Python",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " is",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " a",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " great",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " language",
        "isThinking": false,
        "isSoftStop": true,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}"""

        # Real sample from response.txt
        self.real_sample = """{
    "result": {
        "userResponse": {
            "responseId": "2517e0bf-efd0-4a94-b396-e514dbdd4917",
            "message": "What are some real-world applications built with Python?",
            "sender": "human",
            "createTime": "2025-03-06T11:40:33.571871947Z",
            "parentResponseId": "8a60082c-d206-4102-a2c2-1781ba06345b",
            "manual": false,
            "partial": false,
            "shared": false,
            "query": "",
            "queryType": "",
            "webSearchResults": [],
            "xpostIds": [],
            "xposts": [],
            "generatedImageUrls": [],
            "imageAttachments": [],
            "fileAttachments": [],
            "cardAttachmentsJson": [],
            "fileUris": [],
            "fileAttachmentsMetadata": [],
            "isControl": false,
            "steps": [],
            "mediaTypes": []
        },
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "2517e0bf-efd0-4a94-b396-e514dbdd4917"
    }
}{
    "result": {
        "token": "Python",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": "'s",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " versatility",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": ",",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " ease",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " of",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " use",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": ",",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " and",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " rich",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}"""

        # Sample of a single JSON response
        self.standard_sample = """{
    "response": {
        "responseId": "abc123",
        "message": {
            "content": "This is a sample response"
        },
        "isThinking": false,
        "isSoftStop": true
    }
}"""

        # Sample of invalid JSON
        self.invalid_sample = "This is not a JSON object"

        # Sample with malformed JSON objects
        self.malformed_sample = """{
    "result": {
        "token": " Python",
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}{
    "result": {
        "token": " is
        "isThinking": false,
        "isSoftStop": false,
        "responseId": "beb2b7f8-8ae4-44ae-8613-1b0865b98513"
    }
}"""

    def test_streaming_response_parsing(self):
        """Test parsing of streaming response format."""
        result = self.parser.parse_response(self.streaming_sample)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'streaming')
        self.assertEqual(result['chunks_count'], 5)
        self.assertEqual(result['valid_chunks_count'], 5)
        self.assertEqual(len(result['tokens']), 5)
        self.assertEqual(result['text'], " Python is a great language")
        self.assertEqual(result['response_id'], "beb2b7f8-8ae4-44ae-8613-1b0865b98513")
        self.assertTrue(result['is_complete'])  # Last token has isSoftStop=true
    
    def test_real_sample_parsing(self):
        """Test parsing of a real sample from response.txt."""
        result = self.parser.parse_response(self.real_sample)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'streaming')
        self.assertEqual(result['chunks_count'], 11)  # 11 JSON objects in the sample
        self.assertEqual(result['valid_chunks_count'], 11)  # All should be valid
        self.assertEqual(len(result['tokens']), 10)  # 10 tokens (first object is userResponse)
        self.assertEqual(result['text'], "Python's versatility, ease of use, and rich")
        self.assertEqual(result['response_id'], "beb2b7f8-8ae4-44ae-8613-1b0865b98513")
        
    def test_standard_response_parsing(self):
        """Test parsing of standard (single JSON) response format."""
        result = self.parser.parse_response(self.standard_sample)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'standard')
        self.assertIn('data', result)
        self.assertEqual(result['data']['response']['responseId'], "abc123")
        
    def test_invalid_response_parsing(self):
        """Test handling of completely invalid response."""
        result = self.parser.parse_response(self.invalid_sample)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['format'], 'unknown')
        self.assertIn('message', result)
        
    def test_malformed_response_parsing(self):
        """Test handling of partially malformed response."""
        result = self.parser.parse_response(self.malformed_sample)
        
        self.assertTrue(result['success'])  # Should succeed because at least one chunk is valid
        self.assertEqual(result['format'], 'streaming')
        self.assertEqual(result['chunks_count'], 2)  # Should identify 2 chunks
        self.assertEqual(result['valid_chunks_count'], 1)  # But only 1 is valid
        self.assertEqual(len(result['tokens']), 1)  # Only 1 token extracted
        self.assertEqual(result['text'], " Python")
        
    def test_conversation_id_extraction(self):
        """Test extraction of conversation ID from URL."""
        url = "https://grok.com/rest/app-chat/conversations/67b1a0f4-ddab-4c83-a66b-0cb29f8566ae/responses"
        conv_id = self.parser.extract_conversation_id(url)
        self.assertEqual(conv_id, "67b1a0f4-ddab-4c83-a66b-0cb29f8566ae")
        
        # Test with invalid URL
        invalid_url = "https://grok.com/chat"
        conv_id = self.parser.extract_conversation_id(invalid_url)
        self.assertIsNone(conv_id)
        
    def test_parser_reset(self):
        """Test parser state reset."""
        # First parse something to set the state
        self.parser.parse_response(self.streaming_sample)
        self.assertEqual(len(self.parser.accumulated_tokens), 5)
        self.assertIsNotNone(self.parser.response_id)
        
        # Now reset and check state
        self.parser.reset()
        self.assertEqual(len(self.parser.accumulated_tokens), 0)
        self.assertIsNone(self.parser.response_id)
        self.assertFalse(self.parser.is_complete)
        
    def test_convenience_function(self):
        """Test the convenience function parse_grok_response."""
        result = parse_grok_response(self.streaming_sample)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['format'], 'streaming')
        self.assertEqual(result['text'], " Python is a great language")


if __name__ == "__main__":
    unittest.main() 
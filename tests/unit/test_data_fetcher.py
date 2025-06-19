"""
Unit tests for the DataFetcher class.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import requests

from src.data_fetcher import DataFetcher, RequestError, ParseError


class TestDataFetcher(unittest.TestCase):
    """Test cases for the DataFetcher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.data_fetcher = DataFetcher()
        
        # Sample valid response data
        self.valid_response_data = {
            "page": {
                "id": "kctbh9vrtdwd",
                "name": "GitHub",
                "url": "https://www.githubstatus.com",
                "updated_at": "2023-01-01T00:00:00Z"
            },
            "incidents": [
                {
                    "id": "test-incident-1",
                    "name": "Test Incident 1",
                    "status": "resolved",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T01:00:00Z",
                    "impact": "minor",
                    "incident_updates": []
                }
            ]
        }

    @patch('requests.get')
    def test_successful_data_retrieval(self, mock_get):
        """Test that incidents are successfully retrieved and parsed."""
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.valid_response_data
        mock_get.return_value = mock_response
        
        # Call the method under test
        result = self.data_fetcher.fetch_incidents()
        
        # Verify the result
        self.assertEqual(result, self.valid_response_data)
        self.assertEqual(len(result['incidents']), 1)
        self.assertEqual(result['incidents'][0]['id'], 'test-incident-1')
        
        # Verify the mock was called with the correct URL
        mock_get.assert_called_once_with(self.data_fetcher.api_url, timeout=30)

    @patch('requests.get')
    def test_http_error_handling(self, mock_get):
        """Test handling of HTTP errors."""
        # Configure the mock to raise an HTTP error
        mock_get.side_effect = requests.exceptions.HTTPError("404 Client Error")
        
        # Verify that the method raises a RequestError
        with self.assertRaises(RequestError):
            self.data_fetcher.fetch_incidents()

    @patch('requests.get')
    def test_connection_error_handling(self, mock_get):
        """Test handling of connection errors."""
        # Configure the mock to raise a connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Verify that the method raises a RequestError
        with self.assertRaises(RequestError):
            self.data_fetcher.fetch_incidents()

    @patch('requests.get')
    def test_timeout_error_handling(self, mock_get):
        """Test handling of timeout errors."""
        # Configure the mock to raise a timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Verify that the method raises a RequestError
        with self.assertRaises(RequestError):
            self.data_fetcher.fetch_incidents()

    @patch('requests.get')
    def test_json_parse_error_handling(self, mock_get):
        """Test handling of JSON parsing errors."""
        # Configure the mock to return an invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        # Verify that the method raises a ParseError
        with self.assertRaises(ParseError):
            self.data_fetcher.fetch_incidents()

    @patch('requests.get')
    def test_unexpected_response_format_handling(self, mock_get):
        """Test handling of unexpected API response format."""
        # Configure the mock to return a response without the 'incidents' key
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"page": {"id": "kctbh9vrtdwd"}}  # Missing 'incidents' key
        mock_get.return_value = mock_response
        
        # Verify that the method raises a ParseError
        with self.assertRaises(ParseError):
            self.data_fetcher.fetch_incidents()


if __name__ == '__main__':
    unittest.main()